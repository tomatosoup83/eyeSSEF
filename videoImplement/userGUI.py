from tkinter import *
#import main

# basic window
root = Tk()
root.title("Pupil Detection GUI")
root.geometry("600x600")


# video file selection
# label
videoSelectionLabel = Label(root, text="video of pupil: ")
videoSelectionLabel.place(x = 10, y = 10)

# entry for file directory
videoSelectionEntry = Entry(root, width = 45)
videoSelectionEntry.place(x=100, y = 10)

# button for browsing
videoSelectionBrowseButton = Button(root, text = "browse")
videoSelectionBrowseButton.place(x = 510, y = 10)

root.mainloop()