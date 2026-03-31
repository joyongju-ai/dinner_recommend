import os
import sys

from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("OPENAI_API_KEY가 .env 파일에 설정되어 있지 않습니다.")
    sys.exit(1)

from graph import app


def main():
    print(" 저녁 메뉴 추천 시스템")
    result = app.invoke({
        "user_input": "",
        "mood": "",
        "preferred_taste": [],
        "cooking_difficulty": "",
        "dietary_restrictions": [],
        "has_restrictions": False,
        "menu_candidates": [],
        "recommendation": "",
        "feedback": "",
        "iteration_count": 0,
    })
    print("\n 맛있는 저녁 되세요!")


if __name__ == "__main__":
    main()
