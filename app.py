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


def icon_file(extension, width=24, height=24):
    """Retrun an html.img of the svg icon for a given extension."""
    filetype = icons.get(extension)
    file_name = f'file_type_{filetype}.svg' if filetype is not None else 'default_file.svg'
    html_tag = html.Img(src=app.get_asset_url(f'icons/{file_name}'),
                        width=width, height=height)
    return html_tag


def nowtimestamp(timestamp, fmt='%b %d, %Y %H:%M'):
    return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)

def get_git_file_status(filename):
    # Git의 status 명령을 실행하고 출력 결과를 파싱합니다.
    git_status = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE).stdout.decode(
        'utf-8')
    committed = subprocess.run(['git', 'status', '--porcelain', filename], stdout=subprocess.PIPE)
    parse = git_status.split()
    if len(parse) >= 3:
        return '??'
    elif git_status.startswith('??'):
        # 파일이 Git 저장소에 추가되지 않았습니다.
        return 'untracked'
    elif git_status.startswith('MM') or git_status.startswith('AM'):
        return '??'
    elif git_status.startswith('A '):
        # 파일이 추가되어 staging area에 있습니다.
        return 'staged'
    elif git_status.startswith('M '):
        # 파일이 수정되어 staging area에 있습니다.
        return 'staged'
    elif git_status.startswith(' M'):
        return 'modified'
    else:
        return 'committed'
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
            meaning.append("not updated")
        elif re.match('M[ MTD]', s):
            meaning.append("updated in index")
        elif re.match('T[ MTD]', s):
            meaning.append("type change in index")
        elif re.match('A[ MTD]', s):
            meaning.append("added to index")
        elif s == "D ":
            meaning.append("deleted from index")
        elif re.match('R[ MTD]', s):
            meaning.append("renamed in index")
        elif re.match('C[ MTD]', s):
            meaning.append("copied in index")
        elif re.match('[MTARC] ', s):
            meaning.append("index and work tree matches")
        elif re.match('[ MTARC]M', s):
            meaning.append("work tree changed since index")
        elif re.match('[ MTARC]T', s):
            meaning.append("type changed in work tree since index")
        elif re.match('[ MTARC]D', s):
            meaning.append("deleted from index")
        elif s == " R":
            meaning.append("renamed in work tree")
        elif s == " C":
            meaning.append("copied in index")
        elif s == "DD":
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
        elif s == "??":
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
            dbc.Col([html.Button('git init', id={'type': 'git_button', 'index': 1}, n_clicks=0, disabled = False),  # git init button 'gitinit-val'
                html.Button('not git repo', id={'type': 'git_button', 'index': 2}, disabled=True),  # is git repo button, but disabled 'is_gitrepo'
                html.Button('check', id={'type': 'git_button', 'index': 3}, value = '', style={"margin-left": "15px"}),  # 'check'
                html.Button('add', id={'type': 'git_button', 'index': 4},  disabled = True,style={"margin-left": "15px"}),  # 'add'
                html.Button('restore', id={'type': 'git_button', 'index': 5},  disabled = True,style={"margin-left": "15px"}),  # 'restore'
                html.Button('unstaged', id={'type': 'git_button', 'index': 6}, n_clicks=0, disabled = True,style={"margin-left": "15px"}),  # 'unstaged'
                html.Button('untracked', id={'type': 'git_button', 'index': 7},  disabled = True,style={"margin-left": "15px"}),  # 'untracked'
                html.Button('delete', id={'type': 'git_button', 'index': 8},  disabled = True,style={"margin-left": "15px"}),
                dcc.Input(id='rename', placeholder = 'Enter a name to replace', debounce=True, value='', type='text',style={"margin-left": "15px"}),
                dcc.Store(id='store', data={}),
                html.Button('rename', id={'type': 'git_button', 'index': 9},  disabled = True),
                dcc.Input(id='commit', placeholder = 'Enter a commit message', debounce=True, value='', type='text',style={"margin-left": "15px"}), # 'commit'
                html.Button('commit', id={'type': 'git_button', 'index': 10}, disabled= False)
                     ]),
            # 'delete'
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
                                      html.Div(id='dummy10', n_clicks=0)
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


@app.callback(
    Output('cwd_files', 'children'),
    Input('cwd', 'children'),
    Input('dummy2', 'n_clicks')
)
def list_cwd_files(cwd, d2_clk):
    path = Path(cwd)
    all_file_details = []
    if path.is_dir():
        if not is_git_repo(path):
            files = sorted(os.listdir(path), key=str.lower)
            for i, file in enumerate(files):
                filepath = Path(file)
                full_path=os.path.join(cwd, filepath.as_posix())
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
        #git repository인 경우..
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
                if status == 'untracked':
                    details['extension'] = icon_file("untracked")
                elif status == 'staged':
                    details['extension'] = icon_file("staged")
                elif status == 'modified':
                    details['extension'] = icon_file("modified")
                elif status == 'committed':
                    details['extension'] = icon_file("committed")
                elif status == '??':
                    details['extension'] = icon_file("??")
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
    d_clk=d_clk+1
    if not is_git_repo(path):
        os.system("cd " + str(path)
                  + " && git init")
    return d_clk

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
    files = sorted(os.listdir(cwd), key=str.lower)
    #if n_clicks is None:
        #raise PreventUpdate
    update_files = []
    if n_clicks == 1:
        for i in range(len(checked)):
            if checked[i]:
                update_files.append(files[i])

    states = [get_git_file_status(i) for i in update_files]
    # d_clk=d_clk+1
    #path = Path(cwd)
    is_git = is_git_repo(cwd)
    if is_git == True:
        msg = 'git repo'
    else:
        msg = 'not git repo'
    #modified --> git add + git restore
    if set(states) and set(states).issubset(set(['modified'])):
        return is_git, msg, False, False, True, True, True, True, True, 0
    # update할 파일이 untracked인 경우 or modified인경우 ==> git add 가능
    elif set(states) and set(states).issubset(set(['modified', 'untracked'])):
        return is_git, msg, False, True, True, True, True, True,True, 0
    # git restore
    # unstaged
    elif set(states) and set(states).issubset(set(['staged'])):
        return is_git, msg, True, True, False, True, True, True, True, 0
    # untracked
    elif set(states) and set(states).issubset(set(['committed'])):
        if len(states) == 1:  # check 1 -> rename able
            return is_git, msg, True, True, True, False, False, False, False, 0
        else:  # multiple check -> rename unable
            return is_git, msg, True, True, True, False, False, True, True, 0
    return is_git, msg, True, True, True, True, True, True, True, 0

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
            os.system("cd " + str(Path(cwd)) + " && git restore " + file)
        return 0, d_clk + 1
    return 0, d_clk

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
            os.system("cd " + str(Path(cwd)) + " && git rm --cached " + file)
        return 0, d_clk + 1
    return 0, d_clk

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
            os.system("cd " + str(Path(cwd)) + " && git rm " + file)
        return 0, d_clk + 1
    return 0, d_clk

if __name__ == '__main__':
    app.run_server(debug=True)