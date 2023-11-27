# Contribution Guidelines

Contributions of all kinds are welcome.

# Types of contributions

## Bug reports

To submit a bug report, please use the [issue tracker](https://github.com/lewoudar/ws/issues).

Before trying to submit an issue, make sure that there is not already a similar one reported.

Your message should contain as much information as possible such as:

- the environment in which you worked (OS name and version, python version, etc...)
- Guidance on how to reproduce the issue. For example a small piece of code that can be run immediately.
- Tell me **what you mean by failure** i.e. what are you expecting to happen.

# Fix a bug

To fix a bug, look at the issues reported and every issue with the label *bug* is open to anyone who would like to
correct it. Look at [code contribution](#code-contribution) section before submitting a pull request.

## Submit feedback

To submit feedback, use the [discussions](https://github.com/lewoudar/ws/discussions) forum. Please **do not use
the issue tracker**, I will just close it.

If you want to propose a new feature:

- explain in detail how it would work.
- keep the scope as narrow as possible to make it easier to develop.
- if you want to propose code, just read below the section [code contribution](#code-contribution).

## Code style

Here are some preferences I have when coding:

- When writing a test function, the name should be as obvious as possible about what we want to test. I prefer the
  formulation `test_should..<expectation>..when..<condition>`. I'm not saying it is the best option all the time, but it
  often tends to be more readable.

## Code contribution

Ready to contribute? Here is how to set up the project for local development.

1. Fork the ws repo on GitHub.

2. Clone your fork locally. If you don't know how to proceed, take a look at
   this [article](https://help.github.com/en/articles/fork-a-repo).

3. Install the dependencies needed by the project. You must first install [poetry](https://python-poetry.org/docs/) on
   your computer. After that, you can run:
    ```shell
    poetry install
    ```

4. Install the pre-commit hooks
   ```shell
   pre-commit install
   ```

5. Create a branch for local development
    ```shell
    git checkout -b name-of-bug-or-feature
    ```

6. Make sure you respect the [code style](#code-style) when developing.

7. When you are done with your work, you need to pass all the tests using [nox](https://nox.thea.codes/en/stable/).
    ```shell
    nox -s lint tests
    ```

8. Commit your changes and push your branch to GitHub. For the commit message, you should use the convention described
   [here](https://medium.com/@menuka/writing-meaningful-git-commit-messages-a62756b65c81). It is the convention
   developed by the angular project. There is just one notable difference I'm adding. The verb must be conjugated **in
   the past tense** because I believe we are talking about a done action and not an action to be performed. Also, for
   the scope, there is no particular set of scopes, so feel free to add what you think suits well your changes. If you
   don't have one in mind, don't put anything.

9. Before submitting the pull request, you should verify that you include tests. There is also a code coverage
   configured with the project. You can check the pull request status to know if your tests cover all the code you
   wrote. If your pull request add functionality, please update the documentation.

10. Submit your pull request through the GitHub website.
