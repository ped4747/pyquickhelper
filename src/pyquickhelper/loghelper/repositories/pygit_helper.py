#-*- coding: utf-8 -*-
"""
@file
@brief  Uses git to get version number.
"""

import os,sys,datetime
import xml.etree.ElementTree as ET

from ..flog import fLOG, run_cmd
from ..convert_helper import str_to_datetime

def IsRepo(location, commandline = True, log = False):
    """
    says if it a repository GIT
    
    @param      location        (str) location
    @param      commandline     (bool) use commandline or not
    @param      log             if True, return the log not a boolean
    @return                     bool
    """
    if location is None :
        location = os.path.normpath(os.path.abspath( os.path.join( os.path.split(__file__)[0], "..", "..", "..", "..")))
        
    try :
        get_repo_version(location, commandline, log = log)
        return True
    except Exception :
        if log :
            return get_repo_version(location, commandline, log = log)
        else :
            return False

class RepoFile :
    """
    mimic a GIT file
    """
    def __init__ (self, **args) :
        """
        constructor
        @param   args       list of members to add
        """
        for k,v in args.items() :
            self.__dict__[k] = v
            
        if "name" in self.__dict__ :
            if '"' in self.name:
                #defa = sys.stdout.encoding if sys.stdout != None else "utf8"
                self.name = self.name.replace('"',"")
                #self.name = self.name.encode(defa).decode("utf-8")
            if "\\303" in self.name:
                # don't know yet how to avoid that
                self.name = self.name.replace(r"\303\251","é") \
                                     .replace(r"\303\250","è") 
            
    def __str__(self):
        """
        usual
        """
        return self.name

def repo_ls(full, commandline = True):
    """
    run ``ls`` on a path
    @param      full            full path
    @param      commandline use command line instead of pysvn
    @return                     output of client.ls
    """

    if not commandline :
        try :
            raise NotImplementedError()
        except Exception as e :
            return repo_ls(full, True)
    else :
        if sys.platform.startswith("win32") :
            cmd = r'"C:\Program Files (x86)\Git\bin\git"' 
        else :
            cmd = 'git' 
        
        cmd += " ls-tree -r HEAD \"%s\"" % full
        out,err = run_cmd(  cmd, 
                            wait = True, 
                            do_not_log = True, 
                            encerror = "strict",
                            encoding = sys.stdout.encoding if sys.stdout != None else "utf8",
                            change_path = os.path.split(full)[0] if os.path.isfile(full) else full,
                            shell = sys.platform.startswith("win32") )
        if len(err) > 0 :
            fLOG ("problem with file ", full, err)
            raise Exception(err)
            
        res = [ RepoFile(name=os.path.join(full,_.strip().split("\t")[-1])) \
                        for _ in out.split("\n") if len(_) > 0]
        return res
            
def __get_version_from_version_txt(path) :
    """
    private function, tries to find a file ``version.txt`` which should
    contains the version number (if svn is not present)
    @param      path        folder to look, it will look to the the path of this file,
                            some parents directories and finally this path
    @return                 the version number
    
    @warning If ``version.txt`` was not found, it throws an exception.
    """
    file = os.path.split(__file__)[0]
    paths = [ file,
               os.path.join(file, ".."),
               os.path.join(file, "..", ".."),
               os.path.join(file, "..", "..", ".."),
               path ]
    for p in paths :
        fp = os.path.join(p, "version.txt")
        if os.path.exists (fp) :
            with open(fp, "r") as f :
                return int(f.read().strip(" \n\r\t")) 
    raise FileNotFoundError("unable to find version.txt in\n" + "\n".join(paths))
    
def get_repo_log (path = None, file_detail = False, commandline = True) :
    """
    get the latest changes operated on a file in a folder or a subfolder
    @param      path            path to look
    @param      file_detail     if True, add impacted files
    @param      commandline     if True, use the command line to get the version number, otherwise it uses pysvn
    @return                     list of changes, each change is a list of 4-uple:
                                    - author
                                    - commit hash [:6]
                                    - date (datetime)
                                    - comment$
                                    - full commit hash
                                    - link to commit (if the repository is http://...)
                    
    The function use a command line if an error occurred. It uses the xml format:
    @code
    <logentry revision="161">
        <author>xavier dupre</author>
        <date>2013-03-23T15:02:50.311828Z</date>
        <msg>pyquickhelper: first version</msg>
        <hash>full commit hash</hash>
    </logentry>
    @endcode
    
    Add link:
    @code
    https://github.com/sdpython/pyquickhelper/commit/8d5351d1edd4a8997f358be39da80c72b06c2272    
    @endcode
    
    More: `git pretty format <http://opensource.apple.com/source/Git/Git-19/src/git-htmldocs/pretty-formats.txt>`_
    """
    if file_detail :
        raise NotImplementedError()
    
    if path is None :
        path = os.path.normpath(os.path.abspath( os.path.join( os.path.split(__file__)[0], "..", "..", "..")))
        
    if not commandline :
        try :
            raise NotImplementedError()
        except Exception: 
            return get_repo_log(path, file_detail, True)
    else :
        if sys.platform.startswith("win32") :
            cmd = r'"C:\Program Files (x86)\Git\bin\git"' 
            cmd += ' log --pretty=format:"<logentry revision=\\"%h\\"><author>%an</author><date>%ci</date><msg>%s</msg><hash>%H</hash></logentry>" ' + path
        else :
            cmd = ['git']
            cmd += ['log', '--pretty=format:<logentry revision="%h"><author>%an</author><date>%ci</date><msg>%s</msg><hash>%H</hash></logentry>', path]

        enc  = sys.stdout.encoding if sys.stdout != None else "utf8"
        out,err = run_cmd(  cmd, 
                            wait = True, 
                            do_not_log = True, 
                            encerror = "strict",
                            encoding = enc,
                            change_path = os.path.split(path)[0] if os.path.isfile(path) else path,
                            shell = sys.platform.startswith("win32") ,
                            preprocess = False)
                            
        if len(err) > 0 :
            fLOG ("problem with file ", path, err)
            raise Exception(err + "\nCMD:\n" + cmd  +"\nOUT:\n" + out + "\nERR:\n" + err)
            
        master = get_master_location(path, commandline)
        if master.endswith(".git") :
            master = master[:-4]
        
        if enc != "utf8" and enc != None:
            by = out.encode(enc)
            out = by.decode("utf8")

        out = out.replace("\n\n","\n")
        out = "<xml>%s</xml>"%out
        try:
            root = ET.fromstring(out)
        except ET.ParseError as ee :
            raise Exception("unable to parse:\n" + out) from ee 
        res = []
        for i in root.iter('logentry'):
            revision    = i.attrib['revision'].strip()
            author      = i.find("author").text.strip()
            t           = i.find("msg").text
            hash        = i.find("hash").text
            msg         = t.strip() if t is not None else "-"
            sdate       = i.find("date").text.strip()
            dt          = str_to_datetime(sdate.replace("T"," ").strip("Z "))
            row         = [author, revision, dt, msg, hash ]
            if master.startswith("http") :
                row.append (master + "/commit/" + hash)
            res.append(row)
        return res
                        
def get_repo_version (path = None, commandline = True, usedate = False, log = False) :
    """
    Get the latest check for a specific path or version number based on the date (is usedate is True)
    If usedate is False, it returns a mini hash (a string then)
    
    @param      path            path to look
    @param      commandline     if True, use the command line to get the version number, otherwise it uses pysvn
    @param      usedate         if True, it uses the date to return a minor version number (1.1.thisone)
    @param      log             if True, returns the output instead of a boolean
    @return                     integer)
    """
    if not usedate:
        last = get_nb_commits(path, commandline)
        return last
    else:
        if path is None :
            path = os.path.normpath(os.path.abspath( os.path.join( os.path.split(__file__)[0], "..", "..", "..")))
            
        if not commandline :
            try :
                raise NotImplementedError()
            except Exception as e :
                return get_repo_version(path, True)
        else :
            if sys.platform.startswith("win32") :
                cmd = r'"C:\Program Files (x86)\Git\bin\git" log --format="%h---%ci"'   # %H for full commit hash
            else :
                cmd = 'git log --format="%h---%ci"' 

            if path is not None : cmd += " \"%s\"" % path
            
            out,err = run_cmd(  cmd, 
                                wait = True, 
                                do_not_log = True, 
                                encerror = "strict",
                                encoding = sys.stdout.encoding if sys.stdout != None else "utf8",
                                change_path = os.path.split(path)[0] if os.path.isfile(path) else path,
                                log_error = False,
                                shell = sys.platform.startswith("win32") )
                                                                                
            if len(err) > 0 :
                if log :
                    fLOG ("problem with file ", path, err)
                if log :
                    return "OUT\n{0}\nERR:{1}".format(out,err)
                else :
                    raise Exception(err)

            lines = out.split("\n")
            lines = [ _.split("---") for _ in lines if len(_) > 0 ]
            temp  = lines[0]
            if usedate :
                dt = str_to_datetime(temp[1].replace("T"," ").strip("Z "))
                dt0 = datetime.datetime(dt.year, 1,1,0,0,0)
                res = "%d" % (dt-dt0).days
            else :
                res = temp[0]
            
            if len(res) == 0 :
                raise Exception("the command 'git help' should return something")
                    
            return res
            
def get_master_location(path = None, commandline = True):
    """
    get the master location
    
    @param      path            path to look
    @param      commandline     if True, use the command line to get the version number, otherwise it uses pysvn
    @return                     integer (check in number)
    """
    if path is None :
        path = os.path.normpath(os.path.abspath( os.path.join( os.path.split(__file__)[0], "..", "..", "..")))
        
    if not commandline :
        try :
            raise NotImplementedError()
        except Exception as e :
            return get_repo_version(path, True)
    else :
        if sys.platform.startswith("win32") :
            cmd = r'"C:\Program Files (x86)\Git\bin\git"'
        else :
            cmd = 'git' 
            
        cmd += " config --get remote.origin.url"

        out,err = run_cmd(  cmd, 
                            wait = True, 
                            do_not_log = True, 
                            encerror = "strict",
                            encoding = sys.stdout.encoding if sys.stdout != None else "utf8",
                            change_path = os.path.split(path)[0] if os.path.isfile(path) else path,
                            log_error = False,
                            shell = sys.platform.startswith("win32") )
                                                                            
        if len(err) > 0 :
            fLOG ("problem with file ", path, err)
            raise Exception(err)
        lines = out.split("\n")
        lines = [ _ for _ in lines if len(_) > 0 ]
        res = lines[0]
        
        if len(res) == 0 :
            raise Exception("the command 'git help' should return something")
                
        return res

def get_nb_commits(path = None, commandline = True):
    """
    returns the number of commit
    
    @param      path            path to look
    @param      commandline     if True, use the command line to get the version number, otherwise it uses pysvn
    @return                     integer
    """
    if path is None :
        path = os.path.normpath(os.path.abspath( os.path.join( os.path.split(__file__)[0], "..", "..", "..")))
        
    if not commandline :
        try :
            raise NotImplementedError()
        except Exception as e :
            return get_repo_version(path, True)
    else :
        if sys.platform.startswith("win32") :
            cmd = r'"C:\Program Files (x86)\Git\bin\git" rev-list HEAD --count'   # %H for full commit hash
        else :
            cmd = 'git rev-list HEAD --count' 

        if path is not None : cmd += " \"%s\"" % path
        
        out,err = run_cmd(  cmd, 
                            wait = True, 
                            do_not_log = True, 
                            encerror = "strict",
                            encoding = sys.stdout.encoding if sys.stdout != None else "utf8",
                            change_path = os.path.split(path)[0] if os.path.isfile(path) else path,
                            log_error = False,
                            shell = sys.platform.startswith("win32") )
                                                                            
        if len(err) > 0 :
            raise Exception("unable to get commit number from path {0}\nERR:\n{1}".format(path,err))

        lines = out.strip()
        try:
            nb = int(lines)
        except ValueError as e :
            raise ValueError("unable to parse: " + lines + "\nCMD:\n" + cmd) from e
        return nb
