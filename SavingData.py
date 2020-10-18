from github import GithubException
from requests import exceptions 
from github import Github
from MongoConnect import *
from tkinter import *
from datetime import *
from functools import partial
import csv
import io
import os
import time
import requests
import glob
import subprocess

lastIssue = -1

def extraiEventos(issue, a):
    verificaQuantRequisicoes(a)
    print("---> Extraindo EVENTOS...")
    events = []

    try:
        e = ''
        for event in issue.get_events():
            verificaQuantRequisicoes(a) 
           
            if(event.actor is None):
                if(event.label is None):
                    e = mountEventJSON(issue.number, 
                                       '-', 
                                       event.created_at, 
                                       event.event, 
                                       '-')
                else:
                    e = mountEventJSON(issue.number, 
                                       '-', 
                                       event.created_at, 
                                       event.event, 
                                       event.label.name)
            else:
                if(event.label is None):
                    e = mountEventJSON(issue.number, 
                                       event.actor.login, 
                                       event.created_at, 
                                       event.event, 
                                       '-')
                else:
                    e = mountEventJSON(issue.number, 
                                       event.actor.login, 
                                       event.created_at, 
                                       event.event, 
                                       event.label.name)
            events.append(e)
    except requests.exceptions.ReadTimeout as aes:
        print('Error de conexão')
        raise
    except requests.exceptions.ConnectionError as aes:
        print('Error de conexão')
        raise 
    except GithubException as d:
        if(d.status == 403):
            print("Limite de requisições atingido ao requisitar evento.")
        raise
    
    return events

def extraiComentarios(issue, a):
    verificaQuantRequisicoes(a)
    comments = []
    try:   
        c = ''
        for comment in issue.get_comments():
            print('----> Extraindo COMENTÁRIOS...')       
            verificaQuantRequisicoes(a)
            reactions = extraiReacoes(comment, a)
            if(comment.user is None):
                c = mountIssueCommentJSON('-', 
                                          comment.created_at, 
                                          comment.body, 
                                          reactions) 
            else: 
                c = mountIssueCommentJSON(comment.user.login, 
                                          comment.created_at, 
                                          comment.body, 
                                          reactions)                       
            comments.append(c)
            
    except GithubException as e:
        if(e.status == 403):
            print("Limite de requisições atingido ao requisitar comentrários.")
        raise
    except requests.exceptions.ReadTimeout as aes:
        print('Erro crítico ao resgatar issue.')
        raise
    except requests.exceptions.ConnectionError as aes2:
        raise

    return comments

def extraiReacoes(r, a):
    verificaQuantRequisicoes(a)
    print('----> ----> Extraindo REAÇÕES...') 
    count = [0, 0, 0, 0, 0, 0, 0, 0]
   
    try:
        for reaction in r.get_reactions():
            verificaQuantRequisicoes(a) 

            if(reaction.content == '+1'):
                count[0] += 1
            elif(reaction.content == 'heart'):
                count[1] += 1
            elif(reaction.content == 'hooray'):
                count[2] += 1
            elif(reaction.content == 'confused'):
                count[3] += 1
            elif(reaction.content == '-1'):
                count[4] += 1
            elif(reaction.content == 'laugh'):
                count[5] += 1
            elif(reaction.content == 'rocket'):
                count[6] += 1
            elif(reaction.content == 'eyes'):
                count[7] += 1
            
    except GithubException as e:
        if(e.status == 403):
            print("Limite de requisições atingido ao requisitar reações.")
        raise
    except requests.exceptions.ConnectionError as aes:
        print('Erro crítico ao resgatar issue.')
        raise
    except requests.exceptions.ReadTimeout as req2:
        print('Erro crítico ao resgatar issue.')
        raise

    return mountReactionsJSON(count[0], 
                              count[1], 
                              count[2], 
                              count[3], 
                              count[4], 
                              count[5], 
                              count[6], 
                              count[7])

def extraiLabel(repo, a):
    print("-> Extraindo LABELS... ")
    verificaQuantRequisicoes(a) 
    labelList = []
    try:
        for label in repo.get_labels():        
            labelList.append(label.name)
        l = mountLabelsJSON(labelList)

    except GithubException as e:
        if(e.status == 403):
            print("Limite de requisições atingido ao requisitar labels.")
        raise
    except requests.exceptions.ReadTimeout as aes:
        print('Erro crítico ao resgatar issue.')
        raise
    except requests.exceptions.ConnectionError as req2:
        print('Erro crítico ao resgatar issue.')
        raise

    return l

requisicoesRestantes = 0

# Function to mine the issue with error handling
def getIssue(iss, repository):
    try:
        issue = repository.get_issue(iss) ###
        return issue
    except GithubException as f:
        if(f.status == 404):
           return None
    except AttributeError as a:
        print('AtributeError exception')
        return None

# Function to retrieve the number of the last issue from the repository

def extractLastIssueNumber(auth, repo, lang):
    issuesOpen = issuesClosed = 0
    
    try:
        repository = auth.get_repo(repo)
        verificaQuantRequisicoes(auth)
        for issue in repository.get_issues(state="all"):
            return int(issue.number)
    except GithubException as d:
        if(d.status == 404):
           f = open('DONT_EXISTS.txt', 'a')
           f.write(str(repo) + '\n')
           f.close()

           if(lang == 'pt'):
               print('Repositório não existe')
           elif(lang == 'en'):
               print('Repository does not exist') 

# Function to retrieve already mined repositories in a json folder and add to the already mined list
def already_mined_list(PATH):
    repos_list = []
    
    for f in glob.glob(os.path.join(PATH, '*json')):
        colName = f.rsplit('/', 1)[-1]
        cllName = colName.replace('***', '/')
        #print(cllName)
        repos_list.append(cllName.replace('.json', ''))
    
    return repos_list


def extractDataFromGithub(key, repo, initialIssue, finalIssue, lang, opFlag, clFlag, comFlag, evtFlag, rctFlag, labelsFlag):    
    repoCount = 0
    global requisicoesRestantes
    global lastIssue
    global lastOne
    lastIssue = 0

    try:
        auth = Github(key)
        requisicoesRestantes = int(auth.rate_limiting[0])
        verificaQuantRequisicoes(auth)
        #for repoID in repoList:
        repository = auth.get_repo(repoID)
        
        if(lang == 'pt'):
            print('Extração do repositorio '+repository.full_name+ ' começou.')
        elif(lang == 'en'):
            print('Extraction of the '+repository.full_name+ ' repository started.')

        verificaQuantRequisicoes(auth) 
        l = extraiLabel(repository, auth)
        #if(labelsFlag == 1):
        #    l = extraiLabel(repository, auth)
        #    if(opFlag == 1):
        if(finalIssue == None):
            return True
        
        while(initialIssue < finalIssue):
            verificaQuantRequisicoes(auth)
            issue = getIssue(initialIssue, repo) # Add call to get the first issue in repository
            if(issue is not None and issue.number is not None):
                lastOne = issue.number
                # Add last repo and issue log to recovery after
                file = open('LOG_LASTissue.txt', 'w')
                file.write(str(repo) + ':' + str(issue.number))
                file.close()


                #issuesList = repository.get_issues()            
                #for issue in issuesList:
                if(findIssue(issue.number, repository.name) is None): 
                #        lastIssue = issue
                    verificaQuantRequisicoes(auth)
                    if(lang == 'pt'):  
                        print('--> Extraindo issue : '+str(issue.number))
                    elif(lang == 'en'):
                        print('--> Mining issue: '+str(issue.number))
                    e = '-'
                    c = '-'
                    r = '-'
                    if(evtFlag == 1):
                         e = extraiEventos(issue, auth)
                    if(comFlag == 1):
                        c = extraiComentarios(issue, auth)
                    if(rctFlag == 1):
                        r = extraiReacoes(issue, auth) 
                        
                    p = mountIssueJSON(repository.name, 
                                        issue.number, 
                                        issue.user.login, 
                                        issue.created_at, 
                                        issue.state, 
                                        issue.title, 
                                        issue.body, 
                                        r, e, c, l)
                    save(p, repository.name)
            initialIssue += 1        
"""            
            if(clFlag == 1):
                issuesList = repository.get_issues(state='closed')
                verificaQuantRequisicoes(auth) 
                for issue in issuesList:
                    if(findIssue(issue.number, repository.name) is None): 
                        lastIssue = issue
                        verificaQuantRequisicoes(auth) 
                        print('--> Extraindo Closed Issue: '+str(issue.number))
                        e = '-'
                        c = '-'
                        r = '-'
                        if(evtFlag == 1):
                            e = extraiEventos(issue, auth)
                        if(comFlag == 1):
                            c = extraiComentarios(issue, auth)
                        if(rctFlag == 1):
                            r = extraiReacoes(issue, auth)
                            
                        p = mountIssueJSON(repository.name, 
                                            issue.number, 
                                            issue.user.login, 
                                            issue.created_at, 
                                            issue.state, issue.title, 
                                            issue.body, 
                                            r, e, c, l)
                        save(p, repository.name)      
            repoCount += 1
    """
        if(iss == issFinal):
            if(lang == 'pt'): 
                print(str(repository.full_name)+" minerado com sucesso!")
            elif(lang == 'en'):
                print(str(repository.full_name)+" repository successfully mined!")

            return True
    except requests.exceptions.ReadTimeout as req:
        print("Erro de conexão")
        return False
    except requests.exceptions.ConnectionError as req2:
        print("Erro de conexão")
        return False      
    except GithubException as f:
        if(f.status == 403):
            print("Limite de requisições atingido ao requisitar issues.")
            return False
        else:
            print("Erro na função principal")
            return False 

def verificaQuantRequisicoes(auth, lang):
    global requisicoesRestantes
    r = 0
    requisicoesRestantes -= 1
    
    if(requisicoesRestantes < 30):
        try:
            r = int(auth.get_rate_limit().core.remaining)
            if(r > 30):
                if(lang == 'pt'):
                    print("~~~~~~~ AJUSTANDO NÚMERO DE REQUISIÇÕES ~~~~~~~")
                elif(lang == 'en'):
                    print("~~~~~~~ Adjusting number of requests ~~~~~~~")
                requisicoesRestantes = r     
        except requests.exceptions.ConnectionError as req:
            if(lang == 'pt'):
                print("Erro de conexão")
            elif(lang == 'en'):
                print("Connection error")
            return False
    
        while(requisicoesRestantes < 30):
            if(lang == 'pt'):
                print("~~~~~~~ AGUARDANDO LIBERAÇÃO DA API ~~~~~~~")
            elif(lang == 'en'):
                print("~~~~~~~ WAITING FOR API ~~~~~~~")    
            time.sleep(1800)
            if(lang == 'pt'):
                print("~~~~~~~ QUANTIDADE DE REQUISIÇÕES LIBERADAS ~~~~~~~")
            elif(lang == 'en'):
                print("~~~~~~~ QUANTITY OF REQUESTS ~~~~~~~")

            try:
                requisicoesRestantes = int(auth.get_rate_limit().core.remaining)
            except requests.exceptions.ConnectionError as req:
                if(lang == 'pt'):
                    print("Erro de conexão")
                elif(lang == 'en'):
                    print("Connection error")
                return False
            if(lang == 'pt'):
                print("~~~~~~~ VERIFICANDO  REQUISIÇÕES ~~~~~~~")
                print(str(requisicoesRestantes)+" dispoíveis.")
            elif(lang == 'en'):
                print("~~~~~~~ Checking requests ~~~~~~~")
                print(str(requisicoesRestantes)+" available.")
    
        