import datetime
import os
import subprocess
from pathlib import Path
import dash_mantine_components as dmc
import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL, Dash, Input, Output, State, callback_context, dcc, html
from dash.exceptions import PreventUpdate
from icons import icons
import re
from collections import defaultdict


def icon_file(extension, width=24, height=24):
    """Retrun an html.img of the svg icon for a given extension."""
    filetype = icons.get(extension)
    file_name = f'file_type_{filetype}.svg' if filetype is not None else 'default_file.svg'
    html_tag = html.Img(src=app.get_asset_url(f'icons/{file_name}'),
                        width=width, height=height)
    return html_tag


def nowtimestamp(timestamp, fmt='%b %d, %Y %H:%M'):
    return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)


# directory의 status를 return
# status기준 ==> committed를 제외한 상태를 바탕으로, 개수가 가장 제일 많은 것을 return
# ex) untracked 3개, modified 2개, staged 1개 --> untracked를 return
def directory_status(filename):
    git_status = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE).stdout.decode(
        'utf-8')
    data = git_status.split()
    dic = defaultdict(int)
    if not data:
        return 'committed'
    for i in range(1, len(data), 2):
        dic[get_git_file_status(data[i])] += 1
    result = sorted(dic.items(), key=lambda x: -x[1])
    return result[0][:-1]


# git status: 파일 상태를 확인
def get_git_file_status(filename):
    # Git의 status 명령을 실행하고 출력 결과를 파싱
    git_status = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE).stdout.decode(
        'utf-8')
    committed = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE)
    parse = git_status.split('\n')
    if len(parse) >= 3:
        for p in parse:
            if len(p) > 0:
                if p[0:2] == '??':
                    return '*?'
                elif p[0:2] == '!!':
                    return '*!'
        return '**'
    elif len(git_status) == 0:
        return ''
    else:
        return git_status[0:2]
    """if len(parse) >= 3:
        return '??'
    elif git_status.startswith('??'):
        # 파일이 Git 저장소에 추가되지 않았음
        return 'untracked'
    elif git_status.startswith('MM') or git_status.startswith('AM'):
        return 'modified'
    elif git_status.startswith('A '):
        # 파일이 추가되어 staging area에 있음
        return 'staged'
    elif git_status.startswith('M '):
        # 파일이 수정되어 staging area에 있음.
        return 'staged'
    elif git_status.startswith(' M'):
        return 'modified'
    else:
        return 'committed'"""


def get_git_status_meaning(filename):
    git_status = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE).stdout.decode(
        'utf-8')
    parse = git_status.split('\n')
    status = []
    meaning = []
    for p in parse:
        status.append(p[:2])
    for s in status:
        if re.match(' [AMD]', s):
            meaning.append("not updated")  # not staged
        elif re.match('M[ MTD]', s):
            meaning.append("staged: updated in index")
        elif re.match('T[ MTD]', s):
            meaning.append("staged: type change in index")
        elif re.match('A[ MTD]', s):
            meaning.append("staged: added to index")
        elif s == "D ":
            meaning.append("staged: deleted from index")
        elif re.match('R[ MTD]', s):
            meaning.append("staged: renamed in index")
        elif re.match('C[ MTD]', s):
            meaning.append("staged: copied in index")

        if re.match('[MTARC] ', s):
            meaning.append("index and work tree matches")
        elif re.match('[ MTARC]M', s):
            meaning.append("modified in work tree since index")
        elif re.match('[ MTARC]T', s):
            meaning.append("type changed in work tree since index")
        elif re.match('[ MTARC]D', s):
            meaning.append("deleted from index")
        elif s == " R":
            meaning.append("renamed in work tree")
        elif s == " C":
            meaning.append("copied in index")

        '''if s == "DD":
            meaning.append("unmerged, both deleted")
        elif s == "AU":
            meaning.append("unmerged, added by us")
        elif s == "UD":
            meaning.append("unmerged, deleted by them")
        elif s == "UA":
            meaning.append("unmerged, added by them")
        elif s == "DU":
            meaning.append("unmerged, deleted by us")
        elif s == "AA":
            meaning.append("unmerged, both added")
        elif s == "UU":
            meaning.append("unmerged, both modified")
            '''
        if s == "??":
            meaning.append("untracked")
        elif s == "!!":
            meaning.append("ignored")
    return meaning


def file_info(path):
    """Get file info for a given path.

    Uncomment the attributes that you want to display.

    Parameters:
    -----------
    path : pathlib.Path object
    """
    file_stat = path.stat()
    d = {
        'chbox': False,
        'extension': path.suffix if not path.name.startswith('.') else path.name,
        'filename': path.name,
        # 'fullpath': str(path.absolute()),
        'size': format(file_stat.st_size, ','),
        'created': nowtimestamp(file_stat.st_ctime),
        'modified': nowtimestamp(file_stat.st_mtime),
        # 'accessed': nowtimestamp(file_stat.st_atime),
        # 'is_dir': str(path.is_dir()),
        # 'is_file': str(path.is_file()),
    }
    return d


# git repository
def is_git_repo(path):
    if not os.path.isdir(path):
        return False
    os.chdir(path)
    if os.path.isdir(".git"):
        return True
    try:
        result = subprocess.run(['git', 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stderr.decode('utf-8')
        # git_status = os.popen("git status").read()
        if "fatal" in output.lower():
            return False
        else:
            return True
    except:
        return False


app = Dash(
    __name__,
    title='Dash File Browser',
    assets_folder='assets',
    meta_tags=[
        {'name': 'description',
         'content': """Dash File Browser - a simple browser for files that is \
used to explore files and folder on the server. This is useful if your users \
need to manipulate and analyze files on the server."""},
    ],
    external_stylesheets=[dbc.themes.FLATLY])

server = app.server
modal_style = {
    'width': '500px',
    'position': 'fixed',
    'top': '50%',
    'left': '50%',
    'transform': 'translate(-50%, -50%)'
}

# button 구현
app.layout = html.Div([
                          html.Link(
                              rel="stylesheet",
                              href="https://cdnjs.cloudflare.com/ajax/libs/github-fork-ribbon-css/0.2.3/gh-fork-ribbon.min.css"),
                          html.A(
                              "Fork me on Github",
                              className="github-fork-ribbon",
                              href="https://github.com/eliasdabbas/dash-file-browser",
                              title="Fork me on GitHub", **{"data-ribbon": "Fork me on GitHub"}),
                          html.Br(), html.Br(),
                          html.Button('branch', id='open-popup-button'),
                          dbc.Modal(
                              id='popup',
                              style=modal_style,
                              children=[
                                  html.Div('Branch Action'),
                                  dbc.Row([dcc.Input(id='branch_name',
                                                     style={'width': '200px', 'margin-left': 'True'},
                                                     placeholder="input branch name"),
                                           dcc.Dropdown(
                                               id='branch_dropdown',
                                               style={'width': '200px', 'margin-left': 'auto'},
                                               options=[]), ]),
                                  dbc.Row(
                                      dbc.Col(
                                          [
                                              html.Button('rename', id='rename_branch', n_clicks=0),
                                              html.Button('create', id='create_branch', n_clicks=0),
                                              html.Button('delete', id='delete_branch', n_clicks=0),
                                              html.Button('checkout', id='checkout_branch', n_clicks=0),
                                          ],
                                          className='d-flex justify-content-center align-items-center',  # 중앙 정렬
                                      ),
                                      justify='center',  # 가로 정렬
                                  ),
                                  html.Button('close', id='close-popup-button', ), ]),

                          html.Button('branch_merge', id='open-popup-button-2'),
                          dbc.Modal(
                              id='popup-2',
                              children=[
                                  html.Div('Branch Merge'),
                                  html.Div(id='current_branch',
                                           style={'margin-top': '10px', 'marginLeft': '20px', 'fontSize': '18px'}),
                                  html.Div('✡ Merge할 branch', style={'display': 'inline-block', 'margin-right': '10px',
                                                                     'marginLeft': '20px', 'fontSize': '18px'}),
                                  dcc.Dropdown(
                                      id='branch_dropdown-2',
                                      style={'width': '200px', 'marginLeft': '10px'},
                                  ),
                                  html.Div([
                                      html.Button('Merge', id='merge_branch', n_clicks=0, style={'width': '100%'}),
                                      html.Button('close', id='close-popup-button-2', style={'width': '100%'})
                                  ], style={'display': 'flex', 'justify-content': 'space-between', 'margin': '20px 0'})
                              ]
                          ),

                          dbc.Row([
                              dbc.Col(lg=1, sm=1, md=1),
                              dbc.Col([
                                  dcc.Store(id='stored_cwd', data=os.getcwd()),
                                  html.H1('Dash File Browser'),
                                  html.Hr(), html.Br(), html.Br(), html.Br(),
                                  html.H5(html.B(html.A("⬆️ Parent directory", href='#',
                                                        id='parent_dir'))),
                                  html.H3([html.Code(os.getcwd(), id='cwd')]),
                                  html.Br(), html.Br(),
                                  dbc.Col([html.Button('git init', id={'type': 'git_button', 'index': 1}, n_clicks=0,
                                                       disabled=False),  # git init button 'gitinit-val'
                                           html.Button('not git repo', id={'type': 'git_button', 'index': 2},
                                                       disabled=True),  # is git repo button, but disabled 'is_gitrepo'
                                           html.Button('check', id={'type': 'git_button', 'index': 3}, value='',
                                                       style={"margin-left": "15px"}),  # 'check'
                                           html.Button('add', id={'type': 'git_button', 'index': 4}, disabled=True,
                                                       style={"margin-left": "15px"}),  # 'add'
                                           html.Button('restore', id={'type': 'git_button', 'index': 5}, disabled=True,
                                                       style={"margin-left": "15px"}),  # 'restore'
                                           html.Button('unstaged', id={'type': 'git_button', 'index': 6}, n_clicks=0,
                                                       disabled=True, style={"margin-left": "15px"}),  # 'unstaged'
                                           html.Button('untracked', id={'type': 'git_button', 'index': 7},
                                                       disabled=True, style={"margin-left": "15px"}),  # 'untracked'
                                           html.Button('delete', id={'type': 'git_button', 'index': 8}, disabled=True,
                                                       style={"margin-left": "15px"}),  # 'delete'
                                           dcc.Input(id='rename', placeholder='Enter a name to replace', debounce=True,
                                                     value='', type='text', style={"margin-left": "15px"}),
                                           dcc.Store(id='store', data={}),
                                           html.Button('rename', id={'type': 'git_button', 'index': 9}, disabled=True),
                                           # 'rename'
                                           dcc.Input(id='commit', placeholder='Enter a commit message', debounce=True,
                                                     value='', type='text', style={"margin-left": "15px"}),  # 'commit'
                                           html.Button('commit', id={'type': 'git_button', 'index': 10}, disabled=False)
                                           ]),
                                  dcc.ConfirmDialog(
                                      id='confirm',
                                      message='Are you sure you want to delete this item?',
                                  ),
                                  html.Div(id='commit_message'),

                                  html.Div(id='cwd_files',
                                           style={'height': 500, 'overflow': 'scroll'}),
                              ], lg=10, sm=11, md=10)
                          ])
                      ] + [html.Br() for _ in range(13)] + [html.Div(id='dummy2', n_clicks=0),
                                                            html.Div(id='dummy3', n_clicks=0),
                                                            html.Div(id='dummy4', n_clicks=0),
                                                            html.Div(id='dummy5', n_clicks=0),
                                                            html.Div(id='dummy6', n_clicks=0),
                                                            html.Div(id='dummy7', n_clicks=0),
                                                            html.Div(id='dummy8', n_clicks=0),
                                                            html.Div(id='dummy9', n_clicks=0),
                                                            html.Div(id='dummy10', n_clicks=0),
                                                            html.Div(id='b1', n_clicks=0),  # delete용
                                                            dbc.Modal(id='delete_popup', children=[], ),
                                                            html.Div(id='b2', n_clicks=0),  # checkout용
                                                            dbc.Modal(id='checkout_popup', children=[], ),
                                                            html.Div(id='dummy11', n_clicks=0),
                                                            html.Div(id='b3', n_clicks=0),  # checkout용
                                                            dbc.Modal(id='create_popup', children=[], ),
                                                            html.Div(id='b4', n_clicks=0),  # checkout용
                                                            dbc.Modal(id='rename_popup', children=[], ),
                                                            html.Div(id='m1', n_clicks=0),  # merge용
                                                            dbc.Modal(id='merge_popup', children=[], ),
                                                            ])


@app.callback(
    Output('cwd', 'children'),
    Input('stored_cwd', 'data'),
    Input('parent_dir', 'n_clicks'),
    Input('cwd', 'children'),
    prevent_initial_call=True)
def get_parent_directory(stored_cwd, n_clicks, currentdir):
    triggered_id = callback_context.triggered_id
    if triggered_id == 'stored_cwd':
        return stored_cwd
    parent = Path(currentdir).parent.as_posix()
    return parent


# parent directory를 가져옴
@app.callback(
    Output('cwd_files', 'children'),
    Input('cwd', 'children'),
    Input('dummy2', "n_clicks"),
    Input('dummy4', "n_clicks"),
    Input('dummy5', "n_clicks"),
    Input('dummy6', "n_clicks"),
    Input('dummy7', "n_clicks"),
    Input('dummy8', "n_clicks"),
    Input('dummy9', "n_clicks"),
    Input('dummy10', "n_clicks")
)
def list_cwd_files(cwd, clk_d2, clk_d4, clk_d5, clk_d6, clk_d7, clk_d8, clk_d9, clk_d10):
    path = Path(cwd)
    all_file_details = []
    if path.is_dir():
        if not is_git_repo(path):
            files = sorted(os.listdir(path), key=str.lower)
            for i, file in enumerate(files):
                filepath = Path(file)
                full_path = os.path.join(cwd, filepath.as_posix())
                is_dir = Path(full_path).is_dir()
                link = html.A([
                    html.Span(
                        file, id={'type': 'listed_file', 'index': i},
                        title=full_path,
                        style={'fontWeight': 'bold', 'fontSize': 18} if is_dir else {}
                    )], href='#')
                details = file_info(Path(full_path))
                details['chbox'] = dmc.Checkbox(id={'type': 'dynamic-checkbox', 'index': i}, checked=False)
                details['filename'] = link
                if is_dir:
                    details['extension'] = html.Img(
                        src=app.get_asset_url('icons/default_folder.svg'),
                        width=25, height=25)
                else:
                    details['extension'] = icon_file(details['extension'][1:])
                all_file_details.append(details)
        # git repository인 경우
        else:
            files = sorted(os.listdir(path), key=str.lower)
            for i, file in enumerate(files):
                filepath = Path(file)
                full_path = os.path.join(cwd, filepath.as_posix())
                is_dir = Path(full_path).is_dir()
                link = html.A([
                    html.Span(
                        file, id={'type': 'listed_file', 'index': i},
                        title=full_path,
                        style={'fontWeight': 'bold', 'fontSize': 18} if is_dir else {}
                    )], href='#')
                details = file_info(Path(full_path))
                details['chbox'] = dmc.Checkbox(id={'type': 'dynamic-checkbox', 'index': i}, checked=False)
                details['filename'] = link
                status = get_git_file_status(file)

                #
                if file == '.git':
                    details['extension'] = icon_file('.git')
                elif is_dir:
                    details['extension'] = html.Img(
                        src=app.get_asset_url('icons/default_folder.svg'),
                        width=25, height=25)
                    result = directory_status(file)
                    result = result[0]
                    app.logger.info(result)
                    if result == '':
                        details['status'] = 'committed'
                    elif result == '??':
                        details['status'] = 'untracked'
                    elif result == '!!':
                        details['status'] = 'ignored'
                    elif result[0] in ['M', 'T', 'A', 'R', 'C']:
                        details['extension'] = icon_file("staged")
                        string = ''
                        result1 = get_git_status_meaning(file)
                        for i in range(len(result1)):
                            string += result1[i]
                            if i != len(result1) - 1:
                                string += " && "
                        details['status'] = string
                    elif result[0] == ' ':  # to implement delete, rename, type change later
                        if result[1] == 'M':
                            details['extension'] = icon_file("modified")
                    elif result in ['**', '*?', '*!']:
                        details['extension'] = icon_file("question")
                        string = ''
                        result1 = get_git_status_meaning(file)
                        for i in range(len(result1)):
                            string += result1[i]
                            if i != len(result1) - 1:
                                string += " && "
                        details['status'] = string
                elif status == '':
                    details['extension'] = icon_file("committed")
                elif status == '??':
                    details['extension'] = icon_file("untracked")
                elif status == '!!':
                    details['extension'] = icon_file("ignored")  #need ignored icons
                elif status[0] in ['M', 'T', 'A', 'R', 'C']:
                    details['extension'] = icon_file("staged")
                    string = ''
                    result = get_git_status_meaning(file)
                    for i in range(len(result)):
                        string += result[i]
                        if i != len(result) - 1:
                            string += " && "
                    details['status'] = string
                elif status[0] == ' ':  # to implement delete, rename, type change later
                    if status[1] == 'M':
                        details['extension'] = icon_file("modified")
                elif status in ['**', '*?', '*!']:
                    details['extension'] = icon_file("question")
                    string = ''
                    result = get_git_status_meaning(file)
                    for i in range(len(result)):
                        string += result[i]
                        if i != len(result) - 1:
                            string += " && "
                    details['status'] = string
                all_file_details.append(details)

    df = pd.DataFrame(all_file_details)
    df = df.rename(columns={"extension": ''})
    table = dbc.Table.from_dataframe(df, striped=False, bordered=False,
                                     hover=True, size='sm')
    return html.Div(table)


# 클릭한 파일의 이름을 반환
@app.callback(
    Output('stored_cwd', 'data'),
    Input({'type': 'listed_file', 'index': ALL}, 'n_clicks'),
    State({'type': 'listed_file', 'index': ALL}, 'title'))
def store_clicked_file(n_clicks, title):
    if not n_clicks or set(n_clicks) == {None}:
        raise PreventUpdate
    ctx = callback_context
    index = ctx.triggered_id['index']
    return title[index]


# git init
@app.callback(
    Output('dummy2', "n_clicks"),
    Input({'type': 'git_button', 'index': 1}, 'n_clicks'),
    State('cwd', 'children'),
    State('dummy2', "n_clicks")
)
def git_init(n_clicks, cwd, d_clk):
    if n_clicks == 0:
        raise PreventUpdate
    path = Path(cwd)
    d_clk = d_clk + 1
    if not is_git_repo(path):
        os.system("cd " + str(path)
                  + " && git init")
    return d_clk


# checkbox를 활용해 command할 파일 선택
@app.callback(
    Output({'type': 'git_button', 'index': 1}, 'disabled'),  # git_init
    Output({'type': 'git_button', 'index': 2}, 'children'),  # is_git_repo
    Output({'type': 'git_button', 'index': 4}, 'disabled'),  # git_add
    Output({'type': 'git_button', 'index': 5}, 'disabled'),  # git_restore
    Output({'type': 'git_button', 'index': 6}, 'disabled'),  # git_unstaged
    Output({'type': 'git_button', 'index': 7}, 'disabled'),  # git_untracked
    Output({'type': 'git_button', 'index': 8}, 'disabled'),  # git_delete
    Output('rename', 'disabled'),
    Output({'type': 'git_button', 'index': 9}, 'disabled'),  # git_rename
    Output({'type': 'git_button', 'index': 3}, 'n_clicks'),
    Input({'type': 'git_button', 'index': 3}, 'n_clicks'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    Input('cwd', 'children')
)
def check(n_clicks, checked, cwd):
    btn_able = []
    if not os.path.isdir(cwd):
        return True, 'file', True, True, True, True, True, True, True, 0
    files = sorted(os.listdir(cwd), key=str.lower)
    # if n_clicks is None:
    # raise PreventUpdate
    update_files = []

    is_git = is_git_repo(cwd)
    if is_git == True:
        msg = 'git repo'
    else:
        msg = 'not git repo'

    if n_clicks == 1:
        for i in range(len(checked)):
            if checked[i]:
                if os.path.isdir(cwd+'/'+files[i]):
                    return is_git, msg, True, True, True, True, True, True, True, 0
                update_files.append(files[i])

        if len(update_files) == 0:
            return is_git, msg, True, True, True, True, True, True, True, 0

        states = [get_git_file_status(i) for i in update_files]

        # committed
        if set(states) and set(states).issubset(set([''])):
            if len(states) == 1:  # check 1 -> rename able
                return is_git, msg, True, True, True, False, False, False, False, 0
            else:  # multiple check --> rename unable
                return is_git, msg, True, True, True, False, False, True, True, 0

        btn_able = [is_git, msg, True, True, True, True, True, True, True, 0]
        flag = 1
        for s in states:
            if len(s) == 0:
                break
            if s[0] in [' ', '?', '!']:
                flag = 0
                break
        if flag == 1:  # if all checked files are staged
            btn_able[4] = False

        # modified --> git add + git restore
        if set(states) and set(states).issubset(set([' M', 'MM', 'TM', 'AM', 'RM', 'CM'])):
            btn_able[2] = False
            btn_able[3] = False
            # return is_git, msg, False, False, True, True, True, True, True, 0
        # update할 파일이 untracked인 경우 or modified인경우 --> git add 가능
        elif set(states) and set(states).issubset(set([' M', 'MM', 'TM', 'AM', 'RM', 'CM', '??', '*?'])):
            btn_able[2] = False
            # return is_git, msg, False, True, True, True, True, True, True, 0
        return btn_able
    return is_git, msg, True, True, True, True, True, True, True, 0


# Add (git add) [ untracked -> staged / modified -> staged ]
@app.callback(
    Output({'type': 'git_button', 'index': 4}, 'n_clicks'),
    Output('dummy4', 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    State('dummy4', 'n_clicks'),
    Input({'type': 'git_button', 'index': 4}, 'n_clicks')
)
def git_add(value, checked, cwd, d_clk, n_clicks):
    if n_clicks == 1:
        files = sorted(os.listdir(cwd), key=str.lower)
        staged = []
        for i in range(len(checked)):
            if checked[i] == True:
                staged.append(files[i])
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git add " + '"' + file + '"')
        return 0, d_clk + 1
    return 0, d_clk


# Restore (git restore) [ modified -> unmodified ]
@app.callback(
    Output({'type': 'git_button', 'index': 5}, 'n_clicks'),
    Output('dummy5', 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    State('dummy5', 'n_clicks'),
    Input({'type': 'git_button', 'index': 5}, 'n_clicks')
)
def git_restore(value, checked, cwd, d_clk, n_clicks):
    if n_clicks == 1:
        files = sorted(os.listdir(cwd), key=str.lower)
        staged = []
        for i in range(len(checked)):
            if checked[i] == True:
                staged.append(files[i])
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git restore " + '"' + file + '"')
        return 0, d_clk + 1
    return 0, d_clk


# Unstaged  (git rm --cached) (git restore --staged) [ staged -> modified or untracked ]
@app.callback(
    Output({'type': 'git_button', 'index': 6}, 'n_clicks'),
    Output('dummy6', 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    State('dummy6', 'n_clicks'),
    Input({'type': 'git_button', 'index': 6}, 'n_clicks')
)
def git_unstaged(value, checked, cwd, d_clk, n_clicks):
    if n_clicks == 1:
        files = sorted(os.listdir(cwd), key=str.lower)
        staged = []
        d_clk = d_clk + 1
        for i in range(len(checked)):
            if checked[i] == True:
                staged.append(files[i])
        try:
            os.system("cd " + str(Path(cwd)))
            # d = os.getcwd()
            # os.system("git log --pretty=oneline")
            result = subprocess.run(['git', 'log', '--pretty=oneline'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stderr.decode('utf-8')
            # git_log = os.popen("git log --pretty=oneline").read()
            if "fatal" in output.lower():
                for file in staged:
                    os.system("cd " + str(Path(cwd)) + " && git rm --cached " + '"' + file + '"')
            else:
                for file in staged:
                    os.system("cd " + str(Path(cwd)) + " && git restore --staged " + '"' + file + '"')
        except:
            return 0, d_clk
    return 0, d_clk


# Untracked (git rm --cached) [ unmodified -> untracked ]
@app.callback(
    Output({'type': 'git_button', 'index': 7}, 'n_clicks'),
    Output('dummy7', 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    State('dummy7', 'n_clicks'),
    Input({'type': 'git_button', 'index': 7}, 'n_clicks')
)
def git_untracked(value, checked, cwd, d_clk, n_clicks):
    if n_clicks == 1:
        files = sorted(os.listdir(cwd), key=str.lower)
        staged = []
        for i in range(len(checked)):
            if checked[i] == True:
                staged.append(files[i])
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git rm --cached " + '"' + file + '"')
        return 0, d_clk + 1
    return 0, d_clk


# delete (git rm) [ unmodified -> staged ]
@app.callback(
    Output({'type': 'git_button', 'index': 8}, 'n_clicks'),
    Output('dummy8', 'n_clicks'),
    State({'type': 'git_button', 'index': 3}, 'value'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    State('dummy8', 'n_clicks'),
    Input({'type': 'git_button', 'index': 8}, 'n_clicks')
)
def git_delete(value, checked, cwd, d_clk, n_clicks):
    if n_clicks == 1:
        files = sorted(os.listdir(cwd), key=str.lower)
        staged = []
        for i in range(len(checked)):
            if checked[i] == True:
                staged.append(files[i])
        for file in staged:
            os.system("cd " + str(Path(cwd)) + " && git rm " + '"' + file + '"')
        return 0, d_clk + 1
    return 0, d_clk


# rename
@app.callback(
    Output({'type': 'git_button', 'index': 9}, 'n_clicks'),
    Output('dummy9', 'n_clicks'),
    State({'type': 'dynamic-checkbox', 'index': ALL}, 'checked'),
    State('cwd', 'children'),
    State('dummy9', 'n_clicks'),
    Input({'type': 'git_button', 'index': 9}, 'n_clicks'),
    State('rename', 'value')
)
def git_rename(checked, cwd, n_clicks, d_clk, value):
    if n_clicks:
        index = 0
        for i in range(len(checked)):
            if checked[i]:
                index = i
                break
        files = sorted(os.listdir(cwd), key=str.lower)
        os.system("cd " + str(Path(cwd)) + " && git mv " + '"' + files[index] + '"' + " " + '"' + value + '"')
        return 0, d_clk + 1
    return 0, d_clk


# commit 버튼 누를 경우 팝업
@app.callback(Output('confirm', 'displayed'),
              Output('confirm', 'message'),
              Input({'type': 'git_button', 'index': 10}, 'n_clicks'))
def update_output(n_clicks):
    if n_clicks:
        return True, os.popen("git status").read()
    return False, ''


# Commit (git commit -m "") [Staged -> Committed]
@app.callback(
    Output({'type': 'git_button', 'index': 10}, 'n_clicks'),
    Output('dummy10', 'n_clicks'),
    State('cwd', 'children'),
    State('commit', 'value'),
    State('dummy10', 'n_clicks'),
    Input('confirm', 'submit_n_clicks')
)
def git_commit(cwd, value, d_clk, submit_n_clicks):
    if submit_n_clicks:
        files = sorted(os.listdir(cwd), key=str.lower)
        os.system("cd " + str(Path(cwd)) + " && git commit -m \"" + value + "\"")
        return 0, d_clk + 1
    return 0, d_clk

def find_branch():
    result = os.popen("git branch").read()
    result1 = os.popen("git branch -r").read()
    local, remote = [], []
    local = [i.strip() for i in result.split('\n') if "(HEAD detached at" not in i and i]
    if result1:
        remote = [i.strip() for i in result1.split('\n') if "->" not in i and i]

    return local + remote

@app.callback(
    Output('popup', 'is_open'),
    Output('branch_dropdown', 'options'),
    Output('open-popup-button', 'n_clicks'),
    Output('close-popup-button', 'n_clicks'),
    Input('open-popup-button', 'n_clicks'),
    Input('close-popup-button', 'n_clicks'),
    Input('b1', 'n_clicks'),
    Input('b2', 'n_clicks'),
    Input('b3', 'n_clicks'),
    Input('b4', 'n_clicks'),
    State('popup', 'is_open')
)  # 오픈용..
def toggle_popup(open_clicks, close_clicks, is_open, b1, b2, b3, b4):
    if open_clicks:
        branch = find_branch()
        return True, branch, 0, 0
    return False, [], 0, 0
@app.callback(
    Output('dummy11', 'n_clicks'),
    Output('b2', 'n_clicks'),
    Output('checkout_popup', 'is_open'),
    Output('checkout_popup', 'children'),
    Input('checkout_branch', 'n_clicks'),
    State('branch_dropdown', 'value'),
    State('cwd', 'children'),
    State('dummy11', 'n_clicks'),
    State('b2', 'n_clicks'),
)
def checkout_branch(click, value, cwd, d_clk, b2):
    if value:
        if value[0] == "*":
            value = value[1:].strip()
        app.logger.info(value)
        os.system('cd ' + str(Path(cwd)))
        command = ["git", "checkout", value]
        data = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if not str(data.stderr):
            data = data.stdout
        else:
            data = data.stderr
        if not data:    
            data = 'checkout branch to ' + value
        return d_clk + 1, b2 + 1, True, str(data)
    return d_clk, b2, False, []

def find_branch_merge():
    result = os.popen("git branch").read()
    result1 = os.popen("git branch -r").read()
    local, remote = [], []
    local = [i.strip() for i in result.split('\n') if "(HEAD detached at" not in i and not i.startswith("*")and i.strip()]
    if result1:
        remote = [i.strip() for i in result1.split('\n') if "->" not in i and not i.startswith("*")and i.strip()]

    return local + remote

if __name__ == '__main__':
    app.run_server(debug=True)