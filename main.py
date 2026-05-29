from dotenv import load_dotenv
load_dotenv()

from graph.graph import app


def main():
    question = "My car doesn't start in the winter"
    
    result = app.invoke({"question": question})
    
    print("\n" + "=" * 50)
    print(result["generation"])
    print("=" * 50)


if __name__ == "__main__":
    main()