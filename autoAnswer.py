import json
from get_token import get_token
import requests
from get_course_data import fetch_course_data, save_course_data_to_json


# 读取配置文件
def read_config():
    with open("config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        username = config["username"]
        password = config["password"]
        course_name = config["course_name"]
        homework_title = config["homework_title"]
        print("\n[+] 读取配置文件成功")
        print(f"    账号: {username}")
        print(f"    密码: {password}")
        print(f"    课程名称: {course_name}")
        print(f"    作业标题: {homework_title}")
        print("-" * 40)
        return username, password, course_name, homework_title


# 获取作业ID
def get_homework_id(token, course_name, homework_title):
    print("\n[+] 开始获取课程数据")
    course_data = fetch_course_data(token)
    if course_data:
        print("[+] 课程数据获取成功")
        save_course_data_to_json(course_data)
        print(f"[+] 开始寻找【{course_name}】的【{homework_title}】的作业ID")
        for course in course_data.get("data", []):
            for homework in course["homework"]:
                if homework["title"] == homework_title:
                    print(f"[+] 找到作业ID: {homework['_id']}")
                    print("-" * 40)
                    return homework["_id"]
        print(f"[-] 未找到【{course_name}】的【{homework_title}】的作业ID")
        print("-" * 40)
        return None
    else:
        print("[-] 课程数据获取失败")
        print("-" * 40)
        return None


# 获取已知id作业的题目内容
def get_question_data(token, homework_id):
    url = "https://v2.api.z-xin.net/stu/homework/" + homework_id
    print(f"[+] 开始获取作业【{homework_id}】的内容")
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response = response.json()
    if response.get("code") == 2000:
        print(f"[+] 作业ID【{homework_id}】内容获取成功")
        return response.get("data")
    else:
        print(f"[-] 作业ID【{homework_id}】内容获取失败")
        return None


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


# 获取作业得分
def get_homework_score(token, homework_id):
    # print(f"[+] 开始获取作业【{homework_id}】的得分")
    course_data = fetch_course_data(token)
    if course_data:
        final_score = find_final_score(course_data, homework_id)
        if final_score:
            print(f"[+] 作业得分获取成功，作业【{homework_id}】得分: {final_score}")
            return final_score
        else:
            print(f"[-] 作业【{homework_id}】得分为0")
            return 0
    else:
        print(f"[-] 作业得分获取失败")
        return None


# 获取questionSet_id
def get_questionSet_id(question_data):
    question_sets = question_data.get("questionSets", [])
    if not question_sets:
        raise ValueError("数据中未找到questionSets。")
    return question_sets[0]["_id"]


# 提交作业并输出爆破出该题目的正确答案
def submit_homework(token, homework_id, question_id, questionSet_id):
    last_score = get_homework_score(token, homework_id)

    if last_score is None:
        print("[-] 无法获取初始分数，提交失败")
        return None

    if last_score == 100:
        print(f"[+] 题目【{question_id}】已获得满分，跳过爆破")
        return None

    url = "https://v2.api.z-xin.net/stu/question/answerForQuestion"

    options = [
        "A",
        "B",
        "C",
        "D",
        "AB",
        "AC",
        "AD",
        "BC",
        "BD",
        "CD",
        "ABC",
        "ABD",
        "ACD",
        "BCD",
        "ABCD",
        "T",
        "F",
    ]

    for option in options:
        stuAnswer = [{"mark": char} for char in option]

        requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question_id": question_id,
                "homework_id": homework_id,
                "questionSet_id": questionSet_id,
                "stuAnswer": stuAnswer,
            },
        )

        print(f"[+] 尝试提交答案: {option}")

        score = get_homework_score(token, homework_id)

        if score is None:
            print("[-] 无法获取分数，提交失败")
            return None

        if score > last_score:
            print(f"[+] 答案爆破成功，选项: {option}")
            print("-" * 40)
            return option

    return None


# 清零作业分数
def reset_homework_score(token, homework_id, question_data):
    print("[+] 开始清零作业分数")
    questionSet_id = get_questionSet_id(question_data)
    for question in question_data["questionSets"][0]["questions"]:
        # 提交一个错误答案以清零分数
        requests.post(
            "https://v2.api.z-xin.net/stu/question/answerForQuestion",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "question_id": question["_id"],
                "homework_id": homework_id,
                "questionSet_id": questionSet_id,
                "stuAnswer": [{"mark": "Z"}],  # 假设"Z"是一个错误答案
            },
        )
    if get_homework_score(token, homework_id) == 0:
        print("[+] 作业分数已清零")
    else:
        print("[-] 作业分数清零失败")
        print("[-] 程序退出")
        exit(0)


if __name__ == "__main__":

    username, password, course_name, homework_title = read_config()

    print("[+] 开始获取token")
    token = get_token(username, password)

    if not token or not isinstance(token, str):
        print("[-] Token 无效，请检查账号或密码。")
        print("-" * 40)
        print("[-] 程序退出")
        exit(0)

    if token:
        print("[+] token授权成功")
        homework_id = get_homework_id(token, course_name, homework_title)
        if homework_id:
            print(
                f"[+] 获取【{homework_title}】的作业id成功，作业id: 【{homework_id}】"
            )
            print("-" * 40)
            question_data = get_question_data(token, homework_id)
            questionSet_id = get_questionSet_id(question_data)
            if question_data:
                reset_homework_score(token, homework_id, question_data)
                print("-" * 40)
                print(f"[+] 获取作业【{homework_id}】的题目内容成功")
                print("-" * 40)
                print(f"[+] 开始爆破【{course_name}】的【{homework_title}】作业")
                print("-" * 40)
                answer_list = []
                for question in question_data["questionSets"][0]["questions"]:
                    print(
                        f"[+] 开始爆破题目【{question['content'][:15]}...】题目ID：{question['_id']}"
                    )
                    answer = submit_homework(
                        token, homework_id, question["_id"], questionSet_id
                    )
                    if answer is None:
                        print(
                            "[-] 爆破失败，作业可能已经满分，请清空作业提交或随意作答将分数拉低（尽量清零）后重试"
                        )
                        break
                    if answer:
                        answer_list.append(answer)
                        print(
                            f"[+] 题目【{question['content'][:15]}...】爆破成功，答案: {answer}"
                        )
                        print("-" * 40)
                    else:
                        print(f"[-] 题目【{question['content'][:15]}...】爆破结束")

                print("-" * 40)
                print(
                    f"[+] 爆破【{course_name}】的【{homework_title}】作业结束，答案: {answer_list}"
                )
                print("-" * 40)
            else:
                print("[-] 题目内容获取失败")
                print("-" * 40)
        else:
            print(
                "[-] 作业id获取失败，由于知新系统限制，只能获取课后作业和课程实验的数据，互动课堂无法爆破"
            )
            print("-" * 40)
    else:
        print("[-] token授权失败")
        print("-" * 40)
        print("[-] 程序退出")
        exit(0)
