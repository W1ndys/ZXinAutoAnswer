import json

# 读取数据
with open("course_data.json", "r", encoding="utf-8") as file:
    course_data = json.load(file)


# 遍历数据以查找目标_id的finalScore
def find_final_score(course_data, homework_id):
    final_score = None  # 初始化
    for course in course_data.get("data", []):
        for homework in course.get("homework", []):
            if homework["_id"] == homework_id:
                # 提取分数
                for student_work in homework.get("studenthomework", []):
                    final_score = student_work.get("finalScore", None)
                    if final_score is not None:  # 提前退出
                        return final_score
    return final_score


print(find_final_score(course_data, "67315a31d2058e001e8fdf9e"))
