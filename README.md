
# Dash File Browser with Git repository management service
## Open Source SW Project #1 (2023-1)

## Feature #1: File explorer (file browser)
The service provides a GUI for browsing files and directories on your computer. 
-   The file browsing starts from the root directory of the computer or the most recently visited 
directory.
- All files and directories included in the current directory are displayed with their icon, name, 
and extension.
-   A user can browse a directory by double clicking its icon.
- (Optional) A user can create, delete, copy, move, and execute files and directories on the 
browser.

## Feature #2: Git repository creation
1. [not git repo] 인 경우, [git init] 버튼을 누르면 Git 저장소와 해당 디렉토리에 .git이라는 하위 디렉토리를 생성할 수 있습니다.
2. [git repo] 인 경우, [git init] 버튼은 비활성화 상태입니다.
### The service supports to turn any local directory into a git repository.
-   It provides a menu for a git repository creation only if a current directory in the browser is 
not managed by git yet.
-   Once the repository creation is requested, the service creates a new git repository for the 
current working directory (git init).

## Feature #3 : Version controlling
1. 원하는 command를 실행하기 위해서는 
- 1) 해당하는 파일을 checkbox로 check합니다. 
- 2) [check] 버튼을 누릅니다. 
- 3) 가능한 command button들이 활성화됩니다.
- 단, [commit] 버튼의 경우, 위의 과정을 따르지 않아도 됩니다.

- commit message를 적은 뒤, [commit] 버튼을 누르면 git status 정보를 포함한 팝업창이 생깁니다.
- 확인을 누르면 git commit command가 실행되고, 취소를 누르면 변화하지 않습니다.
### The service supports the version controlling of a git repository. 
-   Files with different status have a different mark on their icon.
-   It provides a different menu depending on the status of a selected file. 
*   For untracked files:
    *   Adding the new files into a staging area (untracked -> staged; git add)
+   For modified files
    +   Adding the modified files into a staging area (modified -> staged; git add)
    +   Undoing the modification (modified -> unmodified; git restore)
-   For staged files
    -   Unstaging changes (staged -> modified or untracked; git restore --staged)
*   For committed or unmodified files
    *   Untracking files (committed -> untracked; git rm --cached)
    *   Deleting files (committed -> staged; git rm)
    *   Renaming files (committed -> staged; git mv)
-   It provides a separate menu for committing staged changes. 
    *   When a user clicks the commit menu, it shows the list of staged changes.
    *   Once the user confirms the commit, it commits the changes to a repository (git commit)
    *   After the commit, the status of the staged files is changed as committed.

## Important Notes
__(주의)원하는 command를 입력하고 싶다면 반드시 checkbox에 check한 뒤, [check] 버튼을 사용해야합니다!__

- Programming language: Python과 dash 프레임워크를 사용
- Platform to run: Web
- Python wrapper를 사용하기 위해 Git CLI와 호환되는 Python 3.6 이상을 추천합니다.
- Git 버전은 Git CLI와의 호환성을 유지하기 위해 최신 버전을 사용하는 것을 추천합니다.
- 운영체제는 Mac, Linux, Windows 모두에서 사용할 수 있지만, Unix 기반 시스템에서 실행할 때 가장 잘 작동합니다.

A simple file browser for Plotly Dash applications.
- Allow users to interactively browse files and folders on the server
- Show folder icons for differentiation
- Expose files and folder as objects to be manipulated by your Dash app

## To run: 

```bash
pip install -r requirements.txt
python app.py

또는

pip3 install -r requirements.txt
python3 app.py
```

## 설치되는 항목
```bash
dash
dash_mantine_components
dash-bootstrap-components
pandas
```
