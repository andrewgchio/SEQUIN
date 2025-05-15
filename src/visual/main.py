# main.py

import view

# MVC Utility functions
View = lambda : view.View()

def run():
    View().start()

if __name__ == "__main__":
    run()
