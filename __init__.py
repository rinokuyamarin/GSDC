from flask import Flask

def main():
    app = Flask(__name__)
    app.run(debug=True)

if __name__ == "__main__":
    main()


