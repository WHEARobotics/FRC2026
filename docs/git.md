# Normal workflow

* Pull any changes from the cloud GitHub repository. **Always** do this at the start of a programming session
  and consider doing it multiple times per session on days when others are also programming.
    1. In VS Code, Click the "Source Control" icon (looks like a branch)
    2. Click the "..." menu (three dots)
    3. Select "Pull" to get the latest code from GitHub
This ensures you have everyone else's changes. If there is a "merge conflict" error, see "Resolving merge conflicts" below.
* If there were changes to `pyproject.toml`, execute `robotpy sync` to get
  the latest wpilib, robotpy, etc. code, both for your computer and ready
  for when you deploy to a robot.
* Edit and test your code.
* When you have something working, even an intermediate step, make
  a commit.
    1. In VS Code, click the "Source Control" icon
    2. You'll see a list of changed files
    3. Click the "+" next to each file you want to commit. Robotpy often writes other files that you **won't** want to commit, don't add those. 90% of the files will be Python (`.py`), JSON (`.json`), or configuration (`.cfg`) files. 
    4. Type a message describing what you changed (be specific!)
    5. Click the "✓" checkmark above your message to commit
* At the end of a work session (or even better, every time get the next thing working) push your commits.
    1. In VS Code, click the "Source Control" icon
    2. Select "Push" to send changes to GitHub. 

TODO: talk about branching?
{>> LOB: I'm thinking at a later date. My worry is that I know changes come fast and furious at competitions. 
(OTOH, you can make the argument that chaos is exactly when you need branches the most!)
<<}

# Merge conflicts

Merge conflicts happen when two people have modified the same file at
the same time, and then both try to push to GitHub.  The first push
will succeed, but if the changes overlap, you get a merge conflict that
shows up like an error. **Don't panic!** Minor merge conflicts are 
easy to fix. Even if you can't figure out how to resolve them,
you are in no danger of losing any work that has been committed, 
either by you on your machine or that has already been stored on
GitHub.

Merge conflicts are not the end of the world, but they are a little more work
because you need to decide which changes from each edit will be kept.
The best ways to avoid them are:
* Communicate with your teammates, coordinate to not overlap changes
  and let them know when you push changes.
* When you have working changes, commit and push.  Don't leave uncommitted
  changes on your computer for days.
* When you start working on something, pull from the repository before
  editing files.

## Resolving Merge Conflicts

There are a few ways to resolve merge conflicts, including graphical tools. 
But there's no need for anything but your editor. If, when trying to push
your commits or trying to pull changes, you see the following dialog, 
select "Pull then Push". ("Force push" is saying "Nope, I'm certain I'm 
correct, use my stuff without asking anymore.")

![VS Code Merge Conflict dialog](./media/git-conflicts-pull-push-ui.png)

You'll then see a new dialog similar to:

![VS Code pulled conflicts](./media/git-conflicts-notification-ui.png)

The **Git Changes** window shows a list of files with conflicts under **Unmerged Changes**. 
To start resolving conflicts, double-click a file. Each conflicted file will have special 
markers in it that look like:

```
<<<<<<< HEAD
Your code
=======
Their code
>>>>>>> main
```

** There often will be multiple conflicts per file! **

Your job is to replace each of these blocks (including the `<<<<<`, `>>>>>>>>`, and `====` lines) with the
code that you think is correct. 

Generally, you'll quickly see which is correct. For instance, if you replaced a magic number
with a reference to a constant, you might see something like:

```
<<<<<<< HEAD
some_function(CONSTANT)
=======
some_function(42)
>>>>>>> main
```

For that, you'd just replace the whole block with:

```
some_function(CONSTANT)
```

Misspellings, syntax errors, and lots of other things will be equally clear. 

Sometimes things will be more complex. Perhaps one of you added or deleted a whole chunk of code in a part of 
the code that the other person changed and committed since the last time you pulled. In those situations, you
need to understand what they were trying to do. Maybe one of you is correct, but often you'll need to 
take a little bit from one and a little bit from the other.

Once all the conflicts have been resolved, you commit them just like you normally do ("stage" them with the
"+" key) and then choose the "✓" checkmark to commit. This is called a "Merge Commit" and it's doubly-important
to write a clear message explaining **why** you resolved the conflicts the way you did. 

After you've made the Merge Commit, you should be able to push it to GitHub without a problem. 
