# Demo
if __name__ == '__main__':
    import argparse
    from help_desk import HelpDesk

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Help Desk RAG System')
    parser.add_argument('--new-db', action='store_true', 
                       help='Create new database (default: False)')
    
    args = parser.parse_args()

    print("Using Firestore storage and VertexAI. Ensure you have set up your Google Cloud credentials.")
        
    print("Using VertexAI LLM with Firestore storage")
    
    model = HelpDesk(new_db=args.new_db, storage_type="firestore")

    # Get document count from Firestore
    doc_count = model.db.get_document_count()
    
    print(f"Vectorstore contains {doc_count} document chunks")

    prompt = 'What is platform engineering?'
    print(f"\nQuestion: {prompt}")
    #result, sources = model.retrieval_qa_inference(prompt)
    answer = ""
    for chunk in model.retrieval_qa_inference(prompt):
        if chunk:
            answer += chunk
    print("\nAnswer:", answer)
