from dotenv import load_dotenv
load_dotenv()

from graph.graph import app


def main():
    question = input("Enter your question:\n")
    
    result = app.invoke({"question": question})
    
    print("\n" + "=" * 50)
    print(result["generation"])
    print("=" * 50)


if __name__ == "__main__":
    main()