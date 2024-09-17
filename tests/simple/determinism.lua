function permissions(user, pass)
    if user == "admin" and pass == "1b7f2lpq" then
        return "admin", "successfully logged in."
    elseif user == "guest" then
        return "guest", "successfully logged in."
    else
        return nil, "invalid username or password."
    end
end

user = input("login to the system (username): ")
pass = input("login to the system (password): ")
result, message = permissions(user, pass)
if result then
    print("Welcome, " .. result .. "!")
else
    print("Issue: " .. message)
end