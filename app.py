from foodtrack import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)  # Never use debug=True in production
