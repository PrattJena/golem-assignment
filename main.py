from dotenv import load_dotenv
load_dotenv()

from ingestion.sync_catalog import init_database
init_database()

from graph.graph import app


def main():
    question = input("\nEnter your question:\n")
    
    result = app.invoke({"question": question})
    
    print("\n" + "=" * 50)
    print(result["generation"])
    print("=" * 50)


if __name__ == "__main__":
    main()