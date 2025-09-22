import tkinter as tk
from tkinter import messagebox

def show_selection():
    selected_options = []
    if var1.get():
        selected_options.append("选项1")
    if var2.get():
        selected_options.append("选项2")
    if var3.get():
        selected_options.append("选项3")
    
    if selected_options:
        messagebox.showinfo("选择结果", f"您选择了: {', '.join(selected_options)}")
    else:
        messagebox.showinfo("选择结果", "您没有选择任何选项")

# 创建主窗口
root = tk.Tk()
root.title("复选框示例")
root.geometry("300x200")

# 创建变量来存储复选框的状态
var1 = tk.BooleanVar()
var2 = tk.BooleanVar()
var3 = tk.BooleanVar()

# 创建复选框
checkbox1 = tk.Checkbutton(root, text="选项1", variable=var1)
checkbox2 = tk.Checkbutton(root, text="选项2", variable=var2)
checkbox3 = tk.Checkbutton(root, text="选项3", variable=var3)

# 创建提交按钮
submit_button = tk.Button(root, text="提交", command=show_selection)

# 布局组件
checkbox1.pack(pady=5)
checkbox2.pack(pady=5)
checkbox3.pack(pady=5)
submit_button.pack(pady=20)

# 运行主循环
root.mainloop()