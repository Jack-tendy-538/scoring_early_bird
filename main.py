import tkinter as tk
import tkinter.messagebox as ms
import subprocess, yaml, json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta

font_chinese = ('Microsoft YaHei', 10)

class ContinuousScoring:
    """连续考勤评分系统，替代生成器的可序列化类"""
    
    def __init__(self, max_days=7):
        self.scoring = [0]  # 连续出勤天数记录
        self.history = []   # 历史出勤记录
        self.max_days = max_days
        self.current_day = 0
    
    def record_attendance(self, today_arrived):
        """记录当天考勤"""
        if today_arrived:
            self.scoring[-1] += 1
        else:
            self.scoring.append(0)
        
        self.history.append(today_arrived)
        self.current_day += 1
        
        # 只保留最近max_days*2天的记录，避免内存过度增长
        if len(self.history) > self.max_days * 2:
            self.history = self.history[-self.max_days*2:]
    
    def calculate_scores(self):
        """计算3天和7天连续出勤分数"""
        # 使用最近max_days天的记录进行计算
        recent_history = self.history[-self.max_days:] if len(self.history) >= self.max_days else self.history
        
        # 重建连续出勤记录
        scoring = [0]
        for arrived in recent_history:
            if arrived:
                scoring[-1] += 1
            else:
                scoring.append(0)
        
        # 计算分数
        _7_day = sum(1 for j in scoring if j == 7)
        _3_day = sum(1 for j in scoring if 3 <= j < 7)
        
        return _3_day, _7_day
    
    def get_current_streak(self):
        """获取当前连续出勤天数"""
        return self.scoring[-1] if self.scoring else 0
    
    def get_total_attendance(self):
        """获取总出勤天数"""
        return sum(self.history)
    
    def get_attendance_rate(self):
        """获取出勤率"""
        if len(self.history) == 0:
            return 0
        return sum(self.history) / len(self.history)
    
    def reset_data(self):
        """重置数据，开始新的一周"""
        self.scoring = [0]
        self.history = []
        self.current_day = 0
    
    def to_dict(self):
        """转换为可序列化的字典"""
        return {
            'scoring': self.scoring,
            'history': self.history,
            'max_days': self.max_days,
            'current_day': self.current_day
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典恢复对象"""
        obj = cls(data.get('max_days', 7))
        obj.scoring = data.get('scoring', [0])
        obj.history = data.get('history', [])
        obj.current_day = data.get('current_day', 0)
        return obj

class AttendanceSystem:
    """考勤系统主类"""
    
    def __init__(self):
        self.cwd = Path.cwd()
        self.setup_directories()
        self.setting = self.load_settings()
    
    def setup_directories(self):
        """创建必要的目录"""
        if not (self.cwd/'eggs').exists():
            (self.cwd/'eggs').mkdir()
        if not (self.cwd/'bacon').exists():
            (self.cwd/'bacon').mkdir()
        if not (self.cwd/'reports').exists():
            (self.cwd/'reports').mkdir()
    
    def load_settings(self):
        """加载或创建设置文件"""
        settings_file = self.cwd/'bacon/Setting.yml'
    
        if not settings_file.exists():
        # 创建默认设置
            default_settings = {
            'points': {
                '_3_days': 1,
                '_7_days': 3
            },
            'namelist': ['学生1', '学生2', '学生3', '学生4', '学生5', '学生6', '学生7', 
                       '学生8', '学生9', '学生10', '学生11', '学生12', '学生13', '学生14'],
            'display': {
                'columns_per_row': 7  # 每行显示的复选框数量
            }
            }
            # 将默认设置写入文件
            with open(settings_file, 'w', encoding='utf-8') as fp:
                yaml.dump(default_settings, fp, allow_unicode=True)
            return default_settings
        else:
            # 尝试不同的编码读取文件
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
            for encoding in encodings:
                try:
                    with open(settings_file, 'r', encoding=encoding) as fp:
                        return yaml.safe_load(fp)
                except (UnicodeDecodeError, yaml.YAMLError):
                    continue
        
        # 如果所有编码都失败，使用错误处理方式读取
            with open(settings_file, 'r', encoding='utf-8', errors='replace') as fp:
                return yaml.safe_load(fp)
    
    def load_student_data(self, session):
        """加载学生数据"""
        data_file = self.cwd/f'eggs/{session}_data.json'
        
        if data_file.exists():
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 从字典恢复ContinuousScoring对象
            students = {}
            for name, student_data in data.items():
                students[name] = ContinuousScoring.from_dict(student_data)
            
            return students
        else:
            # 创建新的学生数据
            students = {}
            for name in self.setting['namelist']:
                students[name] = ContinuousScoring()
            
            self.save_student_data(session, students)
            return students
    
    def save_student_data(self, session, students):
        """保存学生数据"""
        data_file = self.cwd/f'eggs/{session}_data.json'
        
        # 转换为可序列化的字典
        data = {}
        for name, student in students.items():
            data[name] = student.to_dict()
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def record_attendance(self, session, present_students):
        """记录考勤"""
        students = self.load_student_data(session)
        
        # 更新每个学生的考勤记录
        for name, student in students.items():
            arrived = name in present_students
            student.record_attendance(arrived)
        
        # 保存更新后的数据
        self.save_student_data(session, students)
        
        # 计算并显示分数
        scores = {}
        for name, student in students.items():
            scores[name] = student.calculate_scores()
        
        return scores
    
    def reset_all_data(self):
        """重置所有学生的数据，开始新的一周"""
        sessions = ["morning", "afternoon"]
        for session in sessions:
            students = self.load_student_data(session)
            for student in students.values():
                student.reset_data()
            self.save_student_data(session, students)
    
    def generate_summary_report(self):
        """生成汇总报告并保存为Markdown文件，只显示最终分数"""
        # 加载上午和下午的数据
        morning_students = self.load_student_data("morning")
        afternoon_students = self.load_student_data("afternoon")
        
        # 获取学生列表
        students = self.setting['namelist']
        
        # 准备报告数据
        report_data = []
        
        for name in students:
            morning_student = morning_students.get(name, ContinuousScoring())
            afternoon_student = afternoon_students.get(name, ContinuousScoring())
            
            # 计算各项指标 - 只计算最终分数
            morning_3day, morning_7day = morning_student.calculate_scores()
            afternoon_3day, afternoon_7day = afternoon_student.calculate_scores()
            
            # 计算总分
            total_score = (morning_3day + afternoon_3day) * self.setting['points']['_3_days'] + \
                         (morning_7day + afternoon_7day) * self.setting['points']['_7_days']
            
            report_data.append({
                'name': name,
                'total_score': total_score
            })
        
        # 按总分排序
        report_data.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 生成简化的Markdown表格 - 只显示姓名和总分
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_content = f"""# 考勤汇总报告

**生成时间**: {timestamp}  
**本周结束，开始新的一周**

## 本周最终分数统计

| 排名 | 姓名 | 总分 |
|------|------|------|
"""
        
        for i, data in enumerate(report_data, 1):
            md_content += f"| {i} | {data['name']} | **{data['total_score']}** |\n"
        
        # 添加分数说明
        md_content += f"""

## 分数说明

- 连续出勤3天及以上但不足7天: {self.setting['points']['_3_days']}分/次
- 连续出勤7天: {self.setting['points']['_7_days']}分/次

## 注意

本周考勤数据已重置，下周将重新开始统计。
"""
        
        # 保存Markdown文件
        report_file = self.cwd / 'reports' / f'考勤汇总_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 重置所有数据，开始新的一周
        self.reset_all_data()
        
        return report_file
    
    def load_breakpoint(self, session):
        """加载断点数据"""
        breakpoint_file = self.cwd/'eggs/breakpoint.json'
        
        if breakpoint_file.exists():
            with open(breakpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 返回指定session的暂存数据
            return data.get(session, [])
        else:
            return []
    
    def save_breakpoint(self, session, present_students):
        """保存断点数据"""
        breakpoint_file = self.cwd/'eggs/breakpoint.json'
        
        # 加载现有的断点数据
        if breakpoint_file.exists():
            with open(breakpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        
        # 更新指定session的暂存数据
        data[session] = present_students
        
        # 保存更新后的数据
        with open(breakpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def clear_breakpoint(self, session):
        """清除指定session的断点数据"""
        breakpoint_file = self.cwd/'eggs/breakpoint.json'
        
        if breakpoint_file.exists():
            with open(breakpoint_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 移除指定session的数据
            if session in data:
                del data[session]
            
            # 如果还有其他session的数据，保存；否则删除文件
            if data:
                with open(breakpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                breakpoint_file.unlink()

class AttendanceGUI:
    """考勤系统GUI"""
    
    def __init__(self):
        self.system = AttendanceSystem()
        self.win = tk.Tk()
        self.setup_ui()
        self.attendance_windows = {}  # 存储考勤窗口的引用
    
    def setup_ui(self):
        """设置用户界面"""
        self.win.title("考勤系统")
        self.win.geometry("300x250")
        
        tk.Label(self.win, text='请选择一个操作', font=font_chinese).pack(pady=10)
        tk.Button(self.win, text='上午考勤', command=self.append_morning, 
                 width=15, height=2, font=font_chinese).pack(pady=5)
        tk.Button(self.win, text='下午考勤', command=self.append_afternoon,
                 width=15, height=2, font=font_chinese).pack(pady=5)
        tk.Button(self.win, text='生成汇总报告', command=self.generate_summary,
                 width=15, height=2, bg='lightblue', font=font_chinese).pack(pady=5)
        tk.Label(self.win, text='点击按钮记录考勤', font=font_chinese).pack(pady=10)
    
    def append_morning(self):
        """上午考勤"""
        self.take_attendance("morning", "上午")
    
    def append_afternoon(self):
        """下午考勤"""
        self.take_attendance("afternoon", "下午")
    
    def generate_summary(self):
        """生成汇总报告"""
        try:
            result = ms.askyesno("确认", "生成报告后将重置本周数据并开始新的一周，是否继续?")
            if not result:
                return
            report_file = self.system.generate_summary_report()
            ms.showinfo("报告生成成功", f"汇总报告已生成:\n{report_file}\n\n本周数据已重置，下周将重新开始统计。")
            # 尝试打开报告文件
            try:
                subprocess.Popen(['start', '', str(report_file)], shell=True)
            except:
                pass  # 如果打开失败，忽略错误
        except Exception as e:
            ms.showerror("错误", f"生成报告时出错:\n{str(e)}")
    
    def submit_attendance(self, session, session_name, attendance_win, vars, students_list):
        """提交考勤记录"""
        try:
            # 获取选中的学生
            present_students = [name for name, var in vars.items() if var.get()]
            
            if not present_students:
                ms.showwarning("警告", "请至少选择一名学生")
                return
            
            # 记录考勤
            scores = self.system.record_attendance(session, present_students)
            
            # 清除断点数据
            self.system.clear_breakpoint(session)
            
            # 加载学生数据用于显示
            students_data = self.system.load_student_data(session)
            
            # 显示结果
            result_text = f"{session_name}考勤已记录:\n"
            for name in present_students:
                # 安全检查：确保学生存在于数据中
                if name in students_data:
                    streak = students_data[name].get_current_streak()
                    result_text += f"{name}: 连续出勤{streak}天\n"
                else:
                    result_text += f"{name}: 数据不存在\n"
            
            # 显示分数摘要
            result_text += "\n分数统计:\n"
            for name in students_list:
                if name in scores:
                    score_3, score_7 = scores[name]
                    if score_3 > 0 or score_7 > 0:
                        result_text += f"{name}: 3天{score_3}分, 7天{score_7}分\n"
            
            ms.showinfo("考勤结果", result_text)
            attendance_win.destroy()
            
            # 从窗口字典中移除
            if session in self.attendance_windows:
                del self.attendance_windows[session]
                
        except KeyError as e:
            ms.showerror("数据错误", f"学生数据不完整: {str(e)}\n请检查设置文件中的学生名单。")
        except Exception as e:
            ms.showerror("错误", f"提交考勤时出错:\n{str(e)}")
    
    def save_breakpoint_data(self, session, session_name, vars):
        """保存断点数据（暂存）"""
        try:
            # 获取选中的学生
            present_students = [name for name, var in vars.items() if var.get()]
            
            # 保存到断点文件
            self.system.save_breakpoint(session, present_students)
            
            ms.showinfo("暂存成功", f"{session_name}考勤数据已暂存，下次打开时会自动恢复。")
            
        except Exception as e:
            ms.showerror("错误", f"暂存数据时出错:\n{str(e)}")
    
    def start_auto_submit_timer(self, session, session_name, attendance_win, vars, students):
        """启动自动提交定时器"""
        # 计算目标时间
        now = datetime.now()
        
        if session == "morning":
            target_time = now.replace(hour=7, minute=5, second=0, microsecond=0)
        else:  # afternoon
            target_time = now.replace(hour=13, minute=5, second=0, microsecond=0)
        
        # 如果目标时间已经过去，则设置为明天的同一时间
        if target_time < now:
            target_time += timedelta(days=1)
        
        # 计算等待时间（秒）
        wait_seconds = (target_time - now).total_seconds()
        
        # 创建定时器线程
        timer_thread = threading.Timer(wait_seconds, self.auto_submit, 
                                      [session, session_name, attendance_win, vars, students])
        timer_thread.daemon = True
        timer_thread.start()
        
        # 更新窗口标题显示自动提交时间
        time_str = target_time.strftime("%H:%M")
        attendance_win.title(f"{session_name}考勤 - 自动提交时间: {time_str}")
        
        # 添加倒计时标签
        countdown_label = tk.Label(attendance_win, text=f"自动提交倒计时: {int(wait_seconds//60)}分钟", 
                                  font=font_chinese, fg="blue")
        countdown_label.pack(pady=5)
        
        # 启动倒计时更新
        self.update_countdown(countdown_label, wait_seconds, session, session_name, 
                             attendance_win, vars, students)
    
    def update_countdown(self, label, remaining_seconds, session, session_name, 
                        attendance_win, vars, students):
        """更新倒计时显示"""
        if remaining_seconds > 0 and attendance_win.winfo_exists():
            minutes = int(remaining_seconds // 60)
            seconds = int(remaining_seconds % 60)
            label.config(text=f"自动提交倒计时: {minutes}分{seconds}秒")
            # 1秒后再次更新
            attendance_win.after(1000, self.update_countdown, label, remaining_seconds-1, 
                               session, session_name, attendance_win, vars, students)
    
    def auto_submit(self, session, session_name, attendance_win, vars, students):
        """自动提交考勤"""
        if attendance_win.winfo_exists():
            # 在主线程中执行提交
            attendance_win.after(0, self.submit_attendance, session, session_name, 
                               attendance_win, vars, students)
    
    def take_attendance(self, session, session_name):
        """执行考勤记录"""
        # 创建考勤窗口
        attendance_win = tk.Toplevel(self.win)
        attendance_win.title(f"{session_name}考勤")
        
        # 存储窗口引用
        self.attendance_windows[session] = attendance_win
        
        # 获取学生列表和显示设置
        students = self.system.setting['namelist']
        columns_per_row = self.system.setting.get('display', {}).get('columns_per_row', 7)
        
        # 创建主框架
        main_frame = tk.Frame(attendance_win)
        main_frame.pack(padx=10, pady=10, fill='both', expand=True)
        
        # 标题
        tk.Label(main_frame, text=f"请{session_name}早到的同学自己上来打勾:", 
                font=font_chinese).pack(pady=(0, 10))
        
        # 创建复选框容器
        checkboxes_frame = tk.Frame(main_frame)
        checkboxes_frame.pack(fill='both', expand=True)
        
        vars = {}
        checkbuttons = []
        
        # 创建复选框，按指定列数排列
        for i, name in enumerate(students):
            row = i // columns_per_row
            col = i % columns_per_row
            
            vars[name] = tk.BooleanVar()
            cb = tk.Checkbutton(checkboxes_frame, text=name, variable=vars[name], font=font_chinese)
            cb.grid(row=row, column=col, sticky='w', padx=5, pady=2)
            checkbuttons.append(cb)
        
        # 加载断点数据并恢复选中状态
        breakpoint_students = self.system.load_breakpoint(session)
        for name in breakpoint_students:
            if name in vars:
                vars[name].set(True)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # 暂存按钮
        tk.Button(button_frame, text="暂存", 
                 command=lambda: self.save_breakpoint_data(session, session_name, vars),
                 bg='lightyellow', width=10, font=font_chinese).pack(side='left', padx=5)
        
        # 手动提交按钮
        tk.Button(button_frame, text="立即提交", 
                 command=lambda: self.submit_attendance(session, session_name, attendance_win, vars, students),
                 bg='lightgreen', width=10, font=font_chinese).pack(side='left', padx=5)
        
        # 启动自动提交定时器
        self.start_auto_submit_timer(session, session_name, attendance_win, vars, students)
        
        # 自动调整窗口大小
        attendance_win.update()
        attendance_win.minsize(attendance_win.winfo_width(), attendance_win.winfo_height())
    
    def run(self):
        """运行应用程序"""
        self.win.mainloop()

# 运行应用程序
if __name__ == "__main__":
    app = AttendanceGUI()
    app.run()