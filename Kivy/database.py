# database.py

class Database:
    def __init__(self, filename):
        self.filename = filename
        self.users = None
        self.file = None
        self.load()

    def load(self):
        self.file = open(self.filename, "r")
        self.users = {}

        for line in self.file:
            username,firstName,lastName,password = line.strip().split(";")
            self.users[username] = (firstName, lastName, password)
        
        self.file.close()

    def save(self):
        with open(self.filename, "w") as f:
            for user in self.users:
                f.write(user + ";" + self.users[user][0] + ";" + self.users[user][1] + ";" + self.users[user][2] + "\n")

    #find user in database
    def get_user(self, username):
        if username in self.users:
            return self.users[username]
        else:
            return 0
    
    #create new user
    def add_user(self, username,firstName,lastName,password):
        if username.strip() not in self.users:
            self.users[username.strip()] = (firstName.strip(), lastName.strip(), password.strip())
            self.save()
            return 1
        else:
            ## Username already taken
            return 0

    # Checks if user exists and credentials match for login
    def credentialCheck(self, username, password):
        if (self.get_user(username) != 0):  ## checks if user exists
            return (self.users[username][2] == password) ## returns true if passwords match
        else: 
            return 0
