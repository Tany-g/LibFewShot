# How to contribute to this repository

Feel free to contribute classifiers, backbones , functions and any enhancement.

## Add a method/feature or fix a bug

We recommend that you add a method/feature or fix a bug follow the following guidelines:

1. fork `main` branch of  latest`LibFewShot`;
2. checkout a new branch，whose name should reflect the content intuitively, like `add-method-ProtoNet` of `fix-doc-contribution`;
3. add a new method/feature or fix a bug;
4. check and commit;
5. create a pull request.

Note that if you add a new method, you must:

1. test if the method works properly;
2. provide config file of this new method, and the corresponding 5-way 1-shot and 5-way 5-shot accuracy of miniImageNet dataset.

And it is so much better if you can provide:

1. the 5-way 1-shot and 5-way 5-shot accuracy of other dataset (like tieredImageNet);
2. `model_best.pth` that correspond to each setting and dataset.

We will thank you for your contributions in `README` or other prominent places.

## Use `pre-commit` to check code

Before commit the code, you should make sure that your code could pass [black](https://github.com/psf/black) and [flake](https://github.com/PyCQA/flake8) test. We use **pre-commit** to do test and automatic code revision:

1. first, install pre-commit;
```shell
cd <path-to-LibFewShot>
pip install pre-commit
```

2. run `pre-commit install`;
3. run `pre-commit run --all-files;`

4. modify the code by the warning gived by pre-commit.

## Pull request style

The title of your PR should like followings:

```text
[Method] XXXX XXXX
# OR
[Feature] XXXX XXXX
# OR
[FIX] XXXX XXXX
```
The body of your PR should describe the main content of this PR in EN OR CN.