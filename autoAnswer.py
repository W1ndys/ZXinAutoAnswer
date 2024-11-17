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
        print("[+]读取配置文件成功")
        print("[+]账号：" + username)
        print("[+]密码：" + password)
        print("[+]课程名称：" + course_name)
        print("[+]作业标题：" + homework_title)
        print("--------------------------------")
        return username, password, course_name, homework_title


# 获取作业ID
def get_homework_id(token, course_name, homework_title):
    print("[+]开始获取课程数据")
    course_data = fetch_course_data(token)
    if course_data:
        print("[+]课程数据获取成功")
        save_course_data_to_json(course_data)
        print(f"[+]开始寻找【{course_name}】的【{homework_title}】的作业ID")
        for course in course_data["data"]:
            for homework in course["homework"]:
                if homework["title"] == homework_title:
                    print(f"[+]找到作业ID: {homework['_id']}")
                    print("--------------------------------")
                    return homework["_id"]
        print(f"[-]未找到【{course_name}】的【{homework_title}】的作业ID")
        print("--------------------------------")
        return None
    else:
        print("[-]课程数据获取失败")
        print("--------------------------------")
        return None


# 获取作业内容
def get_question_data(token, homework_id):
    url = "https://v2.api.z-xin.net/stu/homework/" + homework_id
    print(f"[+]开始获取作业内容，请求URL: {url}")
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response = response.json()
    if response.get("code") == 2000:
        print(f"[+]作业ID{homework_id}内容获取成功")
        return response.get("data")
    else:
        print(f"[-]作业ID{homework_id}内容获取失败")
        return None


# 遍历数据以查找目标_id的finalScore
def find_final_score(data, target_id):
    for item in data.get("data", {}):
        for homework in item.get("homework", {}):
            for student_homework in homework.get("studenthomework", {}):
                if student_homework.get("_id") == target_id:
                    return student_homework.get("finalScore", 0)
    return 0


# 获取作业得分
def get_homework_score(token, homework_id):
    url = "https://v2.api.z-xin.net/stu/homework/" + homework_id
    print(f"[+]开始获取作业得分")
    response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    response = response.json()
    print(response)
    if response.get("code") == 2000:
        final_score = find_final_score(response, homework_id)
        print(f"[+]作业得分获取成功")
        return final_score
    else:
        print(f"[-]作业得分获取失败，响应: {response.get('msg')}")
        return 0


# 获取questionSet_id
def get_questionSet_id(question_data):
    return question_data["questionSets"][0]["_id"]


# 提交作业并输出爆破出正确的答案
def submit_homework(
    token, homework_id, question_id, questionSet_id, course_name, homework_title
):

    # 记录本次作业上一次的分数
    last_score = 0
    url = "https://v2.api.z-xin.net/stu/question/answerForQuestion"

    # 定义选项列表
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
    ]

    # 存放爆破出的答案
    answer = []

    for option in options:

        # 使用列表推导式将选项转化为 mark 数组
        stuAnswer = [[{"mark": char} for char in option] for option in options]

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

        print(f"[+]正在爆破【{homework_id}】作业，选项: {option}")

        # 获取本次提交后该作业的分数
        score = get_homework_score(token, homework_id)

        if score > last_score:
            last_score = score
            print(f"[+]题目【{question_id}】爆破成功，答案: {option}，已存入答案列表")
            answer.append(option)
            break

    return answer


if __name__ == "__main__":
    username, password, course_name, homework_title = read_config()
    print("[+]开始获取token")
    token = get_token(username, password)
    if token:
        print("[+]token授权成功")
        homework_id = get_homework_id(token, course_name, homework_title)
        if homework_id:
            question_data = get_question_data(token, homework_id)
            questionSet_id = get_questionSet_id(question_data)
            if question_data:
                print("--------------------------------")
                print(f"[+]开始爆破【{course_name}】的【{homework_title}】作业")
                print("--------------------------------")

                for question in question_data["questionSets"][0]["questions"]:
                    answer = submit_homework(
                        token,
                        homework_id,
                        question["_id"],
                        questionSet_id,
                        course_name,
                        homework_title,
                    )

                print("--------------------------------")
                print(
                    f"[+]爆破【{course_name}】的【{homework_title}】作业成功，答案: {answer}"
                )
                print("--------------------------------")
                print(f"[+]爆破【{course_name}】的【{homework_title}】作业结束")
                print("--------------------------------")
    else:
        print("[-]token授权失败")
