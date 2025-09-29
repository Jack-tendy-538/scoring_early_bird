import tkinter as tk
import tkinter.messagebox as ms
import os, yaml, json
from pathlib import Path
from datetime import datetime, timedelta

class ContinuousScoring:
    #"""连续考勤评分系统，替代生成器的可序列化类"""
    
    def __init__(self, max_days=7):
        self.scoring = [0]  # 连续出勤天数记录
        self.history = []   # 历史出勤记录
        self.max_days = max_days
        self.current_day = 0
    
    def record_attendance(self, today_arrived):
        #"""记录当天考勤"""
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
        #"""计算3天和7天连续出勤分数"""
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
        #"""获取当前连续出勤天数"""
        return self.scoring[-1] if self.scoring else 0
    
    def get_total_attendance(self):
        #"""获取总出勤天数"""
        return sum(self.history)
    
    def get_attendance_rate(self):
        #"""获取出勤率"""
        if len(self.history) == 0:
            return 0
        return sum(self.history) / len(self.history)
    
    def to_dict(self):
        #"""转换为可序列化的字典"""
        return {
            'scoring': self.scoring,
            'history': self.history,
            'max_days': self.max_days,
            'current_day': self.current_day
        }
    
    @classmethod
    def from_dict(cls, data):
        #"""从字典恢复对象"""
        obj = cls(data.get('max_days', 7))
        obj.scoring = data.get('scoring', [0])
        obj.history = data.get('history', [])
        obj.current_day = data.get('current_day', 0)
        return obj

class AttendanceSystem:
    #"""考勤系统主类"""
    
    def __init__(self):
        self.cwd = Path.cwd()
        self.setup_directories()
        self.setting = self.load_settings()
    
    def setup_directories(self):
        #"""创建必要的目录"""
        if not (self.cwd/'eggs').exists():
            (self.cwd/'eggs').mkdir()
        if not (self.cwd/'bacon').exists():
            (self.cwd/'bacon').mkdir()
        if not (self.cwd/'reports').exists():
            (self.cwd/'reports').mkdir()
    
    def load_settings(self):
        #"""加载或创建设置文件"""
        settings_file = self.cwd/'bacon/Setting.yml'
        
        if not settings_file.exists():
            # 创建默认设置
            default_settings = {
                'points': {
                    '_3_days': 1,
                    '_7_days': 3
                },
                'namelist': ['学生1', '学生2', '学生3', '学生4']
            }
            
            with open(settings_file, 'w', encoding='utf-8') as fp:
                yaml.dump(default_settings, fp, allow_unicode=True)
            
            return default_settings
        else:
            with open(settings_file, 'r', encoding='utf-8') as fp:
                return yaml.safe_load(fp)
    
    def load_student_data(self, session):
        #"""加载学生数据"""
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
        #"""保存学生数据"""
        data_file = self.cwd/f'eggs/{session}_data.json'
        
        # 转换为可序列化的字典
        data = {}
        for name, student in students.items():
            data[name] = student.to_dict()
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def record_attendance(self, session, present_students):
        #"""记录考勤"""
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
    
    def generate_summary_report(self):
        #"""生成汇总报告并保存为Markdown文件"""
        # 加载上午和下午的数据
        morning_students = self.load_student_data("morning")
        afternoon_students = self.load_student_data("afternoon")
        
        # 获取学生列表
        students = self.setting['namelist']
        
        # 准备报告数据
        report_data = []
        total_days = max(
            max(len(student.history) for student in morning_students.values()) if morning_students else 0,
            max(len(student.history) for student in afternoon_students.values()) if afternoon_students else 0
        )
        
        for name in students:
            morning_student = morning_students.get(name, ContinuousScoring())
            afternoon_student = afternoon_students.get(name, ContinuousScoring())
            
            # 计算各项指标
            morning_3day, morning_7day = morning_student.calculate_scores()
            afternoon_3day, afternoon_7day = afternoon_student.calculate_scores()
            
            morning_total = morning_student.get_total_attendance()
            afternoon_total = afternoon_student.get_total_attendance()
            
            morning_rate = morning_student.get_attendance_rate() * 100
            afternoon_rate = afternoon_student.get_attendance_rate() * 100
            
            morning_streak = morning_student.get_current_streak()
            afternoon_streak = afternoon_student.get_current_streak()
            
            # 计算总分
            total_score = (morning_3day + afternoon_3day) * self.setting['points']['_3_days'] + \
                         (morning_7day + afternoon_7day) * self.setting['points']['_7_days']
            
            report_data.append({
                'name': name,
                'morning_total': morning_total,
                'morning_rate': f"{morning_rate:.1f}%",
                'morning_streak': morning_streak,
                'morning_3day': morning_3day,
                'morning_7day': morning_7day,
                'afternoon_total': afternoon_total,
                'afternoon_rate': f"{afternoon_rate:.1f}%",
                'afternoon_streak': afternoon_streak,
                'afternoon_3day': afternoon_3day,
                'afternoon_7day': afternoon_7day,
                'total_score': total_score
            })
        
        # 按总分排序
        report_data.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 生成Markdown表格
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md_content = f"""# 考勤汇总报告

**生成时间**: {timestamp}  
**统计天数**: {total_days}天

## 考勤统计表

| 排名 | 姓名 | 上午出勤 | 上午出勤率 | 上午连续 | 上午3天分 | 上午7天分 | 下午出勤 | 下午出勤率 | 下午连续 | 下午3天分 | 下午7天分 | 总分 |
|------|------|----------|------------|----------|-----------|-----------|----------|------------|----------|-----------|-----------|------|
"""
        
        for i, data in enumerate(report_data, 1):
            md_content += f"| {i} | {data['name']} | {data['morning_total']} | {data['morning_rate']} | {data['morning_streak']} | {data['morning_3day']} | {data['morning_7day']} | {data['afternoon_total']} | {data['afternoon_rate']} | {data['afternoon_streak']} | {data['afternoon_3day']} | {data['afternoon_7day']} | **{data['total_score']}** |\n"
        
        # 添加分数说明
        md_content += f"""

## 分数说明

- 连续出勤3天及以上但不足7天: {self.setting['points']['_3_days']}分/次
- 连续出勤7天: {self.setting['points']['_7_days']}分/次

## 统计说明

- 出勤率 = 出勤次数 / 总考勤次数
- 连续出勤天数 = 当前连续出勤天数
- 总分 = (上午3天分 + 下午3天分) × {self.setting['points']['_3_days']} + (上午7天分 + 下午7天分) × {self.setting['points']['_7_days']}
"""
        
        # 保存Markdown文件
        report_file = self.cwd / 'reports' / f'考勤汇总_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return report_file

class AttendanceGUI:
    """考勤系统GUI"""
    
    def __init__(self):
        self.system = AttendanceSystem()
        self.win = tk.Tk()
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        self.win.title("考勤系统")
        self.win.geometry("300x250")
        
        tk.Label(self.win, text='请选择一个操作', font=('Arial', 12)).pack(pady=10)
        tk.Button(self.win, text='上午考勤', command=self.append_morning, 
                 width=15, height=2).pack(pady=5)
        tk.Button(self.win, text='下午考勤', command=self.append_afternoon,
                 width=15, height=2).pack(pady=5)
        tk.Button(self.win, text='生成汇总报告', command=self.generate_summary,
                 width=15, height=2, bg='lightblue').pack(pady=5)
        tk.Label(self.win, text='点击按钮记录考勤', font=('Arial', 10)).pack(pady=10)
    
    def append_morning(self):
        """上午考勤"""
        self.take_attendance("morning", "上午")
    
    def append_afternoon(self):
        """下午考勤"""
        self.take_attendance("afternoon", "下午")
    
    def generate_summary(self):
        """生成汇总报告"""
        try:
            report_file = self.system.generate_summary_report()
            ms.showinfo("报告生成成功", f"汇总报告已生成:\n{report_file}")
        except Exception as e:
            ms.showerror("错误", f"生成报告时出错:\n{str(e)}")
    
    def take_attendance(self, session, session_name):
        """执行考勤记录"""
        # 创建考勤窗口
        attendance_win = tk.Toplevel(self.win)
        attendance_win.title(f"{session_name}考勤")
        attendance_win.geometry("250x300")
        
        # 获取学生列表
        students = self.system.setting['namelist']
        vars = {}
        
        # 创建复选框
        tk.Label(attendance_win, text=f"请选择{session_name}出勤的学生:").pack(pady=10)
        
        for name in students:
            vars[name] = tk.BooleanVar()
            tk.Checkbutton(attendance_win, text=name, variable=vars[name]).pack(anchor='w', padx=20)
        
        def submit():
            # 获取选中的学生
            present_students = [name for name, var in vars.items() if var.get()]
            
            if not present_students:
                ms.showwarning("警告", "请至少选择一名学生")
                return
            
            # 记录考勤
            scores = self.system.record_attendance(session, present_students)
            
            # 显示结果
            result_text = f"{session_name}考勤已记录:\n"
            for name in present_students:
                streak = self.system.load_student_data(session)[name].get_current_streak()
                result_text += f"{name}: 连续出勤{streak}天\n"
            
            # 显示分数摘要
            result_text += "\n分数统计:\n"
            for name in students:
                score_3, score_7 = scores[name]
                if score_3 > 0 or score_7 > 0:
                    result_text += f"{name}: 3天{score_3}分, 7天{score_7}分\n"
            
            ms.showinfo("考勤结果", result_text)
            attendance_win.destroy()
        
        tk.Button(attendance_win, text="提交", command=submit).pack(pady=10)
    
    def run(self):
        """运行应用程序"""
        self.win.mainloop()

# 运行应用程序
if __name__ == "__main__":
    app = AttendanceGUI()
    app.run()
