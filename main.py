import tkinter as tk
import tkinter.messagebox as ms
import os, yaml, json
from pathlib import Path
from datetime import datetime, timedelta

class ContinuousScoring:
    
    def __init__(self, max_days=7):
        self.scoring = [0]  # 连续出勤天数记录
        self.history = []   # 历史出勤记录
        self.max_days = max_days
        self.current_day = 0
    
    def record_attendance(self, today_arrived):
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
        return self.scoring[-1] if self.scoring else 0
    
    def to_dict(self):
        return {
            'scoring': self.scoring,
            'history': self.history,
            'max_days': self.max_days,
            'current_day': self.current_day
        }
    
    @classmethod
    def from_dict(cls, data):
        obj = cls(data.get('max_days', 7))
        obj.scoring = data.get('scoring', [0])
        obj.history = data.get('history', [])
        obj.current_day = data.get('current_day', 0)
        return obj

class AttendanceSystem:
    
    def __init__(self):
        self.cwd = Path.cwd()
        self.setup_directories()
        self.setting = self.load_settings()
    
    def setup_directories(self):
        if not (self.cwd/'eggs').exists():
            (self.cwd/'eggs').mkdir()
        if not (self.cwd/'bacon').exists():
            (self.cwd/'bacon').mkdir()
    
    def load_settings(self):
        settings_file = self.cwd/'bacon/Setting.yml'
        
        if not settings_file.exists():
            # 创建默认设置
            default_settings = {
                'points': {
                    '_3_days': 1,
                    '_7_days': 3
                },
                'namelist': ['sexy', 'stupid', 'sweet', 'sleepy']
            }
            
            with open(settings_file, 'w', encoding='utf-8') as fp:
                yaml.dump(default_settings, fp, allow_unicode=True)
            
            return default_settings
        else:
            with open(settings_file, 'r', encoding='utf-8') as fp:
                return yaml.safe_load(fp)
    
    def load_student_data(self, session):
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
        data_file = self.cwd/f'eggs/{session}_data.json'
        
        # 转换为可序列化的字典
        data = {}
        for name, student in students.items():
            data[name] = student.to_dict()
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def record_attendance(self, session, present_students):
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

class AttendanceGUI:
    
    def __init__(self):
        self.system = AttendanceSystem()
        self.win = tk.Tk()
        self.setup_ui()
    
    def setup_ui(self):
        self.win.title("score early bird")
        self.win.geometry("300x200")
        
        tk.Label(self.win, text='please chhose an option:', font=('Arial', 12)).pack(pady=10)
        tk.Button(self.win, text='morning', command=self.append_morning, 
                 width=15, height=2).pack(pady=5)
        tk.Button(self.win, text='afternoon', command=self.append_afternoon,
                 width=15, height=2).pack(pady=5)
        tk.Label(self.win, text='begin the score.', font=('Arial', 10)).pack(pady=10)
    
    def append_morning(self):
        self.take_attendance("morning", "morning")
    
    def append_afternoon(self):
        self.take_attendance("afternoon", "afternoon")
    
    def take_attendance(self, session, session_name):
        # 创建考勤窗口
        attendance_win = tk.Toplevel(self.win)
        attendance_win.title(f"{session_name} scoring")
        attendance_win.geometry("250x300")
        
        # 获取学生列表
        students = self.system.setting['namelist']
        vars = {}
        
        # 创建复选框
        tk.Label(attendance_win, text=f"Please select student of {session_name} :").pack(pady=10)
        
        for name in students:
            vars[name] = tk.BooleanVar()
            tk.Checkbutton(attendance_win, text=name, variable=vars[name]).pack(anchor='w', padx=20)
        
        def submit():
            # 获取选中的学生
            present_students = [name for name, var in vars.items() if var.get()]
            
            if not present_students:
                ms.showwarning("warning", "you should select student at least once.")
                return
            
            # 记录考勤
            scores = self.system.record_attendance(session, present_students)
            
            # 显示结果
            result_text = f"{session_name} Recorded :\n"
            for name in present_students:
                streak = self.system.load_student_data(session)[name].get_current_streak()
                result_text += f"{name}: {streak} in streak\n"
            
            # 显示分数摘要
            result_text += "\nScore stat:\n"
            for name in students:
                score_3, score_7 = scores[name]
                if score_3 > 0 or score_7 > 0:
                    result_text += f"{name}: 3 day {score_3} points, 7 day{score_7} points\n"
            
            ms.showinfo("result", result_text)
            attendance_win.destroy()
        
        tk.Button(attendance_win, text="submit", command=submit).pack(pady=10)
    
    def run(self):
        self.win.mainloop()

# 运行应用程序
if __name__ == "__main__":
    app = AttendanceGUI()
    app.run()