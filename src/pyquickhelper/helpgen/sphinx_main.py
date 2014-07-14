#-*- coding: utf-8 -*-
"""
@file
@brief Contains the main function to generate the documentation
for a module designed the same way as this one, @see fn generate_help_sphinx.

"""
import os,sys, shutil, datetime, re, importlib
from pandas import DataFrame

from ..loghelper.flog           import run_cmd, fLOG
from ..loghelper.pyrepo_helper  import SourceRepository
from ..pandashelper.tblformat   import df_to_rst
from .utils_sphinx_doc          import prepare_file_for_sphinx_help_generation
from .utils_sphinx_doc_helpers  import HelpGenException
from ..sync.synchelper          import explore_folder

template_examples = """

List of programs
++++++++++++++++
      
.. toctree::
   :maxdepth: 2

.. autosummary:: __init__.py
   :toctree: %s/
   :template: modules.rst
   
Another list
++++++++++++

"""

def generate_help_sphinx (  project_var_name, 
                            clean           = True, 
                            root            = ".",
                            filter_commit   = lambda c : c.strip() != "documentation",
                            extra_ext       = [],
                            nbformats       = ["ipynb", "html", "python", "rst", "pdf"],
                            layout          = ["html"]) :
    """
    runs the help generation
        - copies every file in another folder
        - replaces comments in doxygen format into rst format
        - replaces local import by global import (tweaking sys.path too)
        - calls sphinx to generate the documentation.
        
    @param      project_var_name    project name
    @param      clean               if True, cleans the previous documentation first
    @param      root                see below
    @param      filter_commit       function which accepts a commit to show on the documentation (based on the comment)
    @param      extra_ext           list of file extensions
    @param      nbformats           requested formats for the notebooks conversion
    @param      layout              list of formats sphinx should generate such as html, latex, pdf, docx 
    
    The result is stored in path: ``root/_doc/sphinxdoc/source``.
    We assume the file ``root/_doc/sphinxdoc/source/conf.py`` exists
    as well as ``root/_doc/sphinxdoc/source/index.rst``.
    
    If you generate latex/pdf files, you should add variables ``latex_path`` and ``pandoc_path``
    in your file ``conf.py`` which defines the help.
    
    @code
    latex_path  = r"C:/Program Files/MiKTeX 2.9/miktex/bin/x64"
    pandoc_path = r"%USERPROFILE%/AppData/Local/Pandoc"
    @endcode
    
    @example(run help generation)
    @code
    # from the main folder which contains folder src
    generate_help_sphinx("pyquickhelper")
    @endcode
    @endexample
    
    By default, the function only consider files end by ``.py`` and ``.rst`` but you could
    add others files sharing the same extensions by adding this one
    in the ``extra_ext`` list.
    
    @example(other page of examples___run help generation)
    This example is exactly the same as the previous one but will be generated on another page of examples.
    @code
    # from the main folder which contains folder src
    generate_help_sphinx("pyquickhelper")
    @endcode
    @endexample
    
    @example(page with an accent -é- in the title___run help generation)
    Same page with an accent.
    @code
    # from the main folder which contains folder src
    generate_help_sphinx("pyquickhelper")
    @endcode
    @endexample
    """
    root = os.path.abspath(root)
    froot = root
    sys.path.append (os.path.join(root, "_doc", "sphinxdoc","source"))
    
    src = SourceRepository(commandline=True)
    version = src.version(root)
    if version != None :
        with open("version.txt", "w") as f : f.write(str(version) + "\n")
    
    # modifies the version number in conf.py
    shutil.copy("README.rst", "_doc/sphinxdoc/source")
    shutil.copy("LICENSE.txt", "_doc/sphinxdoc/source")
    
    # import conf.py
    theconf     = importlib.import_module('conf')
    if theconf is None:
        raise ImportError("unable to import conf.py which defines the help generation")
    latex_path  = theconf.__dict__.get("latex_path",r"C:\Program Files\MiKTeX 2.9\miktex\bin\x64")
    pandoc_path = theconf.__dict__.get("pandoc_path",r"%USERPROFILE%\AppData\Local\Pandoc")

    #changes
    chan = os.path.join (root, "_doc", "sphinxdoc", "source", "filechanges.rst")
    generate_changes_repo(chan, root, filter_commit = filter_commit)
    
    # copy the files 
    optional_dirs = [ ]
    
    mapped_function = [ (".*[.]%s$" % ext.strip(".") , None) for ext in extra_ext ]
            
    prepare_file_for_sphinx_help_generation ( 
                {},
                root, 
                "_doc/sphinxdoc/source/", 
                subfolders      = [ 
                                    ("src/" + project_var_name, project_var_name), 
                                     ],
                silent          = True,
                rootrep         = ("_doc.sphinxdoc.source.%s." % (project_var_name,), ""),
                optional_dirs   = optional_dirs,
                mapped_function = mapped_function )
                
    fLOG("**** end of prepare_file_for_sphinx_help_generation")
    
    # notebooks
    notebook_dir = os.path.abspath(os.path.join("_doc", "notebooks"))
    notebook_doc = os.path.abspath(os.path.join("_doc/sphinxdoc/source", "notebooks"))
    if os.path.exists(notebook_dir):
        notebooks = explore_folder(notebook_dir, pattern=".*[.]ipynb", fullname=True)[1]
        notebooks = [ _ for _ in notebooks if "checkpoint" not in _ ]
        if len(notebooks) > 0:
            fLOG("**** notebooks")
            build = os.path.abspath("build/notebooks")
            if not os.path.exists(build): os.makedirs(build)
            if not os.path.exists(notebook_doc): os.mkdir(notebook_doc)
            nbs = process_notebooks(notebooks, 
                                    build=build, 
                                    outfold=notebook_doc,
                                    formats=nbformats,
                                    latex_path=latex_path,
                                    pandoc_path=pandoc_path)
            add_notebook_page(nbs, os.path.join(notebook_doc,"..","all_notebooks.rst"))
            
        imgs      = [ os.path.join(notebook_dir,_) for _ in os.listdir(notebook_dir) if ".png" in _  ]
        if len(imgs) > 0 :
            for img in imgs :
                shutil.copy (img, notebook_doc)
            
                
    #  run the documentation generation
    if sys.platform == "win32" :
        temp = os.environ ["PATH"]
        pyts = get_executables_path()
        script = ";".join(pyts)
        fLOG ("adding " + script)
        temp = script + ";" + temp
        os.environ["PATH"] = temp
        fLOG("changing PATH", temp)
        pa = os.getcwd ()

    thispath = os.path.normpath(root)
    docpath  = os.path.normpath(os.path.join(thispath, "_doc","sphinxdoc"))

    fLOG("checking encoding utf8...")
    for root, dirs, files in os.walk(docpath):
        for name in files:
            thn = os.path.join(root, name)
            if name.endswith(".rst") :
                try :
                    with open(thn, "r", encoding="utf8") as f : f.read()
                except UnicodeDecodeError as e :
                    raise HelpGenException ("issue with encoding for file ", thn) from e
                except Exception as e :
                    raise HelpGenException ("issue with file ", thn) from e
                
    fLOG("running sphinx... from", docpath)
    if not os.path.exists (docpath) :
        raise FileNotFoundError(docpath)
        
    if sys.platform == "win32" :
        make = os.path.join(docpath, "make.bat")
        if not os.path.exists(make) : raise FileNotFoundError(make)
            
    os.chdir (docpath)
    if clean :
        cmd = "make.bat clean".split ()
        run_cmd (cmd, wait = True)
        
    for lay in layout :
        if lay == "pdf":
            lay = "latex"
        cmd = "make {0}".format(lay)
        # This instruction should work but it does not. Sphinx seems to be stuck.
        #run_cmd (cmd, wait = True, secure="make_help.log", stop_waiting_if = lambda v : "build succeeded" in v)
        # The following one works but opens a extra windows.
        os.system(cmd)
        if lay == "latex":
            post_process_latex_output(froot, False)
        
    if "pdf" in layout:
        compile_latex_output_final(froot, latex_path, False)
    
    # end
    os.chdir (pa)
    
def get_executables_path() :
    """
    returns the paths to Python, Python Scripts
    
    @return     a list of paths
    """
    res  = [ os.path.split(sys.executable)[0] ]
    res += [ os.path.join(res[-1], "Scripts") ]
    if sys.platform == "win32" :
        ver = "c:\\Python%d%d" % (sys.version_info.major, sys.version_info.minor)
        res += [ver ]
        res += [ os.path.join(res[-1], "Scripts") ]
    return res
    
def generate_changes_repo(  chan, 
                            source, 
                            exception_if_empty = True,
                            filter_commit = lambda c : c.strip() != "documentation") :
    """
    Generates a rst tables containing the changes stored by a svn or git repository,
    the outcome is stored in a file.
    The log comment must start with ``*`` to be taken into account.
    
    @param          chan                filename to write (or None if you don't need to)
    @param          source              source folder to get changes for
    @param          exception_if_empty  raises an exception if empty
    @param          filter_commit       function which accepts a commit to show on the documentation (based on the comment)
    @return                             string (rst tables with the changes)
    """
    # builds the changes files
    try :
        src = SourceRepository(commandline=True)
        logs = src.log(path = source)
    except Exception as e :
        if exception_if_empty :
            fLOG("error, unable to retrieve log from " + source)
            raise HelpGenException("unable to retrieve log from " + source) from e
        else :
            logs = [ ("none", 0, datetime.datetime.now(), "-") ]
            fLOG("error,",e)

    if len(logs) == 0 :
        fLOG("error, unable to retrieve log from " + source)
        if exception_if_empty:
            raise HelpGenException("retrieved logs are empty from " + source)
    else :
        fLOG("info, retrieved ", len(logs), " commits")
        
    rows = [ ]
    rows.append("""\n.. _l-changes:\n\n\nChanges\n=======\n\nList of recent changes:\n""")

    values = []
    for row in logs :
        code, nbch, date, comment = row[:4]
        last = row[-1]
        if last.startswith("http") :
            nbch = "`%s <%s>`_"% (str(nbch), last)
            
        ds = "%04d-%02d-%02d" % (date.year, date.month, date.day)
        if filter_commit(comment):
            if isinstance(nbch,int) :
                values.append ( ["%04d" % nbch, "%s" % ds, comment.strip("*") ] )
            else :
                values.append ( ["%s" % nbch, "%s" % ds, comment.strip("*") ] )
            
    if len(values) == 0 and exception_if_empty:
        raise HelpGenException("Logs were not empty but there was no comment starting with '*' from " + source + "\n" + "\n".join( [ str(_) for _ in logs ] ))

    if len(values) > 0 :
        tbl = DataFrame ( columns=["change number", "date", "comment"], data=values)
        rows.append("\n\n" + df_to_rst(tbl, align=["1x","1x","3x"]) + "\n\n")

    final = "\n".join(rows)
    if chan != None :
        with open(chan, "w", encoding="utf8") as f :
            f.write(final)
    return final

def process_notebooks(  notebooks, 
                        outfold, 
                        build,
                        latex_path,
                        pandoc_path,
                        formats = ["ipynb", "html", "python", "rst", "pdf"]
                        ):
    """
    converts notebooks into html, rst, latex using 
    `nbconvert <http://ipython.org/ipython-doc/rel-1.0.0/interactive/nbconvert.html>`_.
    
    @param      notebooks   list of notebooks 
    @param      outfold     folder which will contains the outputs
    @param      build       tempoary folder which contains all produced files
    @param      pandoc_path path to pandoc
    @param      formats     list of formats to convert into (pdf format means latex then compilation)
    @param      latex_path  path to the latex compiler
    @return                 created files
    
    This function relies on `pandoc <http://johnmacfarlane.net/pandoc/index.html>`_.
    It also needs modules `pywin32 <http://sourceforge.net/projects/pywin32/>`_,
    `pygments <http://pygments.org/>`_.
    
    `pywin32 <http://sourceforge.net/projects/pywin32/>`_ might have some issues
    to find its DLL, look @see fn import_pywin32.
    
    The latex compilation uses `MiKTeX <http://miktex.org/>`_.
    
    @warning Some latex templates (for nbconvert) uses ``[commandchars=\\\\\\{\\}]{\\|}`` which allows commands ``\\\\`` and it does not compile. 
                The one used here is ``report``.
                
    *Will be deprecated:*
    
    The function can use a different python Version if environement variable ``PANDOCPY`` is set up the Python path.
    `WinPython <http://winpython.sourceforge.net/>`_ works better when a notebook contains an image.
    """
    if isinstance(notebooks,str):
        notebooks = [ notebooks ]

    if "PANDOCPY" in os.environ:
        exe = os.environ["PANDOCPY"]
        exe = exe.rstrip("\\/")
        if exe.endswith("\\Scripts"):
            exe = exe[:len(exe)-len("Scripts")-1]
        if not os.path.exists(exe):
            raise FileNotFoundError(exe)
        fLOG("** using PANDOCPY", exe)
    else :
        if sys.platform.startswith("win"):
            from .utils_pywin32 import import_pywin32   
            import_pywin32()
        exe = os.path.split(sys.executable)[0]
            
    extensions = {  "ipynb":".ipynb",
                    "latex":".tex",
                    "pdf":".pdf",
                    "html":".html",
                    "rst":".rst",
                    "python":".py",
                }
    
    if sys.platform.startswith("win"):
        user = os.environ["USERPROFILE"]
        path = pandoc_path.replace("%USERPROFILE%", user)
        p = os.environ["PATH"]
        if path not in p :
            p += ";%WINPYDIR%\DLLs;" + path 
            os.environ["WINPYDIR"]=exe
            os.environ["PATH"] = p
            
        files = [ ]
        
        ipy = os.path.join(exe, "Scripts", "ipython3.exe")
        cmd = '{0} nbconvert --to {1} "{2}"{5} --output="{3}\\{4}"'
        for notebook in notebooks:
            nbout = os.path.split(notebook)[-1]
            if " " in nbout: raise Exception("spaces are not allowed in notebooks file names: {0}".format(notebook))
            nbout = os.path.splitext(nbout)[0]
            for format in formats :
                
                options = ""
                if format == "pdf": 
                    title = os.path.splitext(os.path.split(notebook)[-1])[0].replace("_", " ")
                    format = "latex"
                    options = ' --post PDF --SphinxTransformer.author="" --SphinxTransformer.overridetitle="{0}"'.format(title)
                    compilation = True
                else :
                    compilation = False
                    
                # output
                outputfile = os.path.join(build, nbout + extensions[format])
                fLOG("--- produce ", outputfile)
                
                # we chech it was not done before
                if os.path.exists(outputfile) :
                    dto = os.stat(outputfile).st_mtime 
                    dtnb = os.stat(notebook).st_mtime
                    if dtnb < dto :
                        fLOG("-- skipping notebook", format, notebook, "(", outputfile, ")")
                        files.append ( outputfile )
                        continue
                
                templ = "full" if format != "latex" else "article"
                fLOG("convert into ", format, " NB: ", notebook)
                
                if format == "html":
                    fmttpl = " --template {0}".format(templ)
                else :
                    fmttpl = ""
                
                c = cmd.format(ipy, format, notebook, build, nbout, fmttpl)

                c += options
                fLOG(c)
                
                #
                if format not in ["ipynb"]:
                    # for latex file
                    if format == "latex":
                        cwd = os.getcwd()
                        os.chdir(build)
                        
                    out,err = run_cmd(c,wait=True, do_not_log = False, log_error=False)
                    
                    if format == "latex": 
                        os.chdir(cwd)
                
                    if "raise ImportError" in err:
                        raise ImportError(err)
                    if len(err)>0 and "error" in err.lower():
                        raise HelpGenException(err)
                        
                    # we should compile a second time
                    # compilation = True  # already done above
                    
                format = extensions[format].strip(".")
                
                # we add the file to the list of generated files
                files.append ( outputfile )
                
                if "--post PDF" in c :
                    files.append ( os.path.join( build, nbout + ".pdf") )
                    
                fLOG("******",format, compilation, outputfile)

                if compilation:
                    # compilation latex
                    if os.path.exists(latex_path):
                        lat = os.path.join(latex_path, "pdflatex.exe")
                        tex = files[-1].replace(".pdf", ".tex")
                        post_process_latex_output_any(tex)
                        c = '"{0}" "{1}" -output-directory="{2}"'.format(lat, tex, os.path.split(tex)[0]) #  -interaction=batchmode
                        fLOG("   ** LATEX compilation (b)", c) 
                        out,err = run_cmd(c,wait=True, do_not_log = False, log_error=False)
                        if len(err) > 0 :
                            raise HelpGenException(err)
                        f = os.path.join( build, nbout + ".pdf")
                        if not os.path.exists(f):
                            raise HelpGenException(err)
                        files.append(f)
                    else:
                        fLOG("unable to find latex in", latex_path)
                        
                elif format == "html":
                    # we add a link to the notebook
                    files += add_link_to_notebook(outputfile, notebook, "pdf" in formats, False, "python" in formats)
                    
                elif format == "ipynb":
                    # we just copy the notebook
                    files += add_link_to_notebook(outputfile, notebook, "ipynb" in formats, 
                                                False, "python" in formats)
                    
                elif format == "rst":
                    # we add a link to the notebook
                    files += add_link_to_notebook(outputfile, notebook, "pdf" in formats, "html" in formats, "python" in formats)
                    
                elif format in ("tex", "latex", "pdf"):
                    files += add_link_to_notebook(outputfile, notebook, False, False, False)
                    
                elif format == "py":
                    pass
                    
                else :
                    raise Exception("unexpected format " + format)
        
        copy = [ ]
        for f in files:
            dest = os.path.join(outfold, os.path.split(f)[-1])
            if not f.endswith(".tex"):
                
                if sys.version_info >= (3,4):
                    try:
                        shutil.copy(f, outfold)
                        fLOG("copy ",f, " to ", outfold, "[",dest,"]")
                    except shutil.SameFileError:
                        fLOG("w,file ", dest, "already exists")
                        pass
                else :
                    try:
                        shutil.copy(f, outfold)
                        fLOG("copy ",f, " to ", outfold, "[",dest,"]")
                    except shutil.Error as e :
                        if "are the same file" in str(e) :
                            fLOG("w,file ", dest, "already exists")
                        else :
                            raise e
                            
                if not os.path.exists(dest):
                    raise FileNotFoundError(dest)
            copy.append ( dest )
            
        # image
        for image in os.listdir(build):
            if image.endswith(".png") or image.endswith(".html") or image.endswith(".pdf"):
                image = os.path.join(build,image)
                dest = os.path.join(outfold, os.path.split(image)[-1])

                if sys.version_info >= (3,4):
                    try:
                        shutil.copy(image, outfold)
                        fLOG("copy ",image, " to ", outfold, "[",dest,"]")
                    except shutil.SameFileError:
                        fLOG("w,file ", dest, "already exists")
                        pass
                else :
                    try:
                        shutil.copy(image, outfold)
                        fLOG("copy ",image, " to ", outfold, "[",dest,"]")
                    except shutil.Error as e:
                        if "are the same file" in str(e) :
                            fLOG("w,file ", dest, "already exists")
                        else :
                            raise e
                        
                if not os.path.exists(dest):
                    raise FileNotFoundError(dest)
                copy.append ( dest )
        
        return copy
    else :
        raise NotImplementedError("not implemented on linux")

def add_link_to_notebook(file, nb, pdf, html, python):
    """
    add a link to the notebook in HTML format and does a little bit of cleaning
    for various format
    
    @param      file        notebook.html
    @param      nb          notebook (.ipynb)
    @param      pdf         if True, add a link to the PDF, assuming it will exists at the same location
    @param      html        if True, add a link to the HTML conversion
    @param      python      if True, add a link to the Python conversion
    @return                 list of generated files
    
    The function does some cleaning too in the files.
    """
    ext = os.path.splitext(file)[-1]
    
    fold,name = os.path.split(file)
    res = [ os.path.join(fold, os.path.split(nb)[-1]) ]
    if not os.path.exists(res[-1]):
        shutil.copy(nb, fold)

    if   ext == ".ipynb": return res
    elif ext == ".html" :
        post_process_html_output(file, pdf, python)
        return res
    elif ext == ".tex" :
        post_process_latex_output(file, True)
        return res
    elif ext == ".rst"  : 
        post_process_rst_output(file, html, pdf, python)
        return res
    else : 
        raise HelpGenException("unable to add a link to this extension: " + ext)

def add_notebook_page(nbs, fileout):
    """
    creates a rst page with links to all notebooks
    
    @param      nbs             list of notebooks to consider
    @param      fileout         file to create
    @return                     created file name
    """
    rst = [ _ for _ in nbs if _.endswith(".rst") ]

    rows = ["", ".. _l-notebooks:","","","Notebooks","=========",""]

    exp = re.compile("[.][.] _([-a-zA-Z0-9_]+):")
    rst = sorted(rst)
    
    rows.append("")
    rows.append(".. toctree::")
    rows.append("")
    for file in rst:
        rows.append("    notebooks/{0}".format(os.path.splitext(os.path.split(file)[-1])[0]))
        
    rows.append("")
    with open(fileout, "w", encoding="utf8") as f :
        f.write("\n".join(rows))
    return fileout
    
def post_process_latex_output(root, doall):
    """
    post process the latex file produced by sphinx
    
    @param      root        root path or latex file to process
    @param      doall       do all transformations
    """
    if os.path.isfile(root):
        file = root
        with open(file, "r", encoding="utf8") as f : content = f.read()
        content = post_process_latex(content, doall)
        with open(file, "w", encoding="utf8") as f : f.write(content)
    else :
        build = os.path.join(root, "_doc", "sphinxdoc","build","latex")
        for tex in os.listdir(build):
            if tex.endswith(".tex"):
                file = os.path.join(build,tex)
                fLOG("modify file", file)
                with open(file, "r", encoding="utf8") as f : content = f.read()
                content = post_process_latex(content, doall)
                with open(file, "w", encoding="utf8") as f : f.write(content)
                
def post_process_latex_output_any(file):
    """
    post process the latex file produced by sphinx
    
    @param      file        latex filename
    """
    fLOG("   ** post_process_latex_output_any ", file)
    with open(file, "r", encoding="utf8") as f : content = f.read()
    content = post_process_latex(content, True)
    with open(file, "w", encoding="utf8") as f : f.write(content)                
            
def post_process_rst_output(file, html, pdf, python):
    """
    process a RST file generated from the conversion of a notebook
    
    @param      file        filename
    @param      pdf         if True, add a link to the PDF, assuming it will exists at the same location
    @param      html        if True, add a link to the HTML conversion
    @param      python      if True, add a link to the Python conversion
    """
    fold,name = os.path.split(file)
    noext = os.path.splitext(name)[0]
    with open(file, "r", encoding="utf8") as f :
        lines = f.readlines()
        
    for pos in range(0,len(lines)):
        lines[pos] = lines[pos].replace(".. code:: python","::")
        
    for pos,line in enumerate(lines):
        line = line.strip("\n\r")
        if len(line) > 0 and line == "=" * len(line):
            lines[pos] = lines[pos].replace("=","*")
            pos2 = pos-1
            l = len(lines[pos])
            while len(lines[pos2])!=l: pos2-=1
            sep = "" if lines[pos2].endswith("\n") else "\n"
            lines[pos2] = "{0}{2}{1}".format(lines[pos],lines[pos2], sep)
            for p in range(pos2+1,pos):
                if lines[p] == "\n": lines[p] = ""
            break
            
    pos += 1
    if pos >= len(lines):
        raise HelpGenException("unable to find a title")
        
    # label
    label = "\n.. _{0}:\n\n".format (name.replace(" ","").replace("_","").replace(":","").replace(".","").replace(",",""))
    lines.insert(0,label)
        
    # links
    links = [ '**Links:**','','    * :download:`notebook <{0}.ipynb>`'.format(noext) ]
    if html: 
        links.append('    * :download:`html <{0}.html>`'.format(noext))
    if pdf: 
        links.append('    * :download:`PDF <{0}.pdf>`'.format(noext))
    if python: 
        links.append('    * :download:`python <{0}.py>`'.format(noext))
    lines[pos] = "{0}\n\n{1}\n\n**Notebook:**\n\n".format(lines[pos],"\n".join(links))
    
    # bullets
    for pos,line in enumerate(lines):
        if pos == 0 : continue
        if len(line) > 0 and (line.startswith("- ") or line.startswith("* ")) \
            and pos < len(lines) :
            next = lines[pos+1]
            prev = lines[pos-1]
            if (next.startswith("- ") or next.startswith("* ")) \
               and not (prev.startswith("- ") or prev.startswith("* ")) \
               and not prev.startswith("  "):
                lines[pos-1] += "\n"
            elif line.startswith("-  ") and next.startswith("   ") \
                 and not prev.startswith("   ") and not prev.startswith("-  "):
                lines[pos-1] += "\n"
    
    # we remove some empty lines
    rem=[]
    for i in range(1,len(lines)-1):
        if len(lines[i].strip(" \n\r")) == 0:
            if lines[i-1][0:2] not in ["..", "  ","::"] and \
               lines[i+1][0:2] not in ["..", "  ","::"] and \
               len(lines[i-1].strip(" \n\r"))>0 and \
               len(lines[i-1][:4] != "    " and \
               lines[i+1].strip(" \n\r"))>0 :
                rem.append(i)
        if len(lines[i]) > 0 and lines[i] != " " and lines[i-1].startswith("    ") :
            lines[i] = "\n" + lines[i]
    rem.reverse()
    for i in rem:
        del lines[i]
        
    # remove last ::
    for i in range(len(lines)-1,0,-1) :
        s = lines[i-1].strip(" \n\r")
        if len(s) != 0 and s != "::"  : break
    
    if i < len(lines):
        del lines[i:]
            
    with open(file, "w", encoding="utf8") as f :
        f.write("".join(lines))
    
def post_process_html_output(file, pdf, python):
    """
    process a HTML file generated from the conversion of a notebook
    
    @param      file        filename
    @param      pdf         if True, add a link to the PDF, assuming it will exists at the same location
    @param      python      if True, add a link to the Python conversion
    """
    fold,name = os.path.split(file)
    noext = os.path.splitext(name)[0]
    with open(file, "r", encoding="utf8") as f :
        text = f.read()
        
    link = '''
            <div style="position:fixed;text-align:center;align:right;width:15%;bottom:50px;right:20px;background:#DDDDDD;">
            <p>
            {0}
            </p>
            </div>
            '''
            
    links = [ '<b>links</b><br /><a href="{0}.ipynb">notebook</a>'.format(noext) ]
    if pdf: 
        links.append( '<a href="{0}.pdf">PDF</a>'.format(noext))
    if python: 
        links.append( '<a href="{0}.py">python</a>'.format(noext))
    link = link.format( "\n<br />".join(links) )
            
    text = text.replace("</body>", link + "\n</body>")
    text = text.replace("<title>[]</title>", "<title>%s</title>" % name)
    if "<h1>" not in text and "<h1 id" not in text : 
        text = text.replace("<body>", "<body><h1>%s</h1>" % name)

    with open(file, "w", encoding="utf8") as f :
        f.write(text)

def post_process_latex(st, doall):
    """
    modifies a latex file after its generation by sphinx
    
    @param      st      string
    @param      doall   do all transformations
    @return             string
    """
    fLOG("   ** enter post_process_latex", doall, "%post_process_latex" in st)
    st = st.replace("<br />","\\\\")
    
    if not doall :
        st = st.replace("\\maketitle","\\maketitle\n\n\\newchapter{Introduction}")
    
    st = st.replace("%5C","/").replace("%3A",":").replace("\\includegraphics{notebooks\\","\\includegraphics{")
    st = st.replace(r"\begin{document}",r"\setlength{\parindent}{0cm}%s\begin {document}" % "\n")
    st = st.replace(r"DefineVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\}}",
                    r"DefineVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\},fontsize=\small}")
    
    # hyperref
    if doall and "%post_process_latex" not in st :
        st = "%post_process_latex\n" + st
        reg = re.compile("hyperref[[]([a-zA-Z0-9]+)[]][{](.*?)[}]")
        allhyp = reg.findall(st)
        sections = [ ]
        for id,section in allhyp:
            sec = r"\subsection{%s} \label{%s}" % (section, id)
            sections.append ( (id,section, sec) )
    elif not doall:
        sections = [ ]
        # first section
        lines = st.split("\n")
        for i,line in enumerate(lines):
            if "\\section" in line :
                lines[i] = "\\newchapter{Documentation}\n" + lines[i]
                break
        st = "\n".join(lines)

    if len(sections) > 0 :
        lines = st.split("\n")
        for i,line in enumerate(lines):
            for id,section,sec in sections :
                if line.strip("\r\n ") == section :
                    fLOG("   **", section, " --> ", sec)
                    lines[i] = sec
        st = "\n".join(lines)
        
    st = st.replace("\\chapter", "\\section")
    st = st.replace("\\newchapter", "\\chapter")
    st = st.replace(r"\usepackage{multirow}", r"\usepackage{multirow}\usepackage{amssymb}\usepackage{latexsym}\usepackage{amsfonts}")
    
    return st
    
def compile_latex_output_final(root, latex_path, doall, afile = None):
    """
    compiles the latex documents
    
    @param      root        root
    @param      latex_path  path to the compiler
    @param      doall       do more transformation of the latex file before compiling it
    @param      afile       process a specific file
    """
    lat = os.path.join(latex_path, "pdflatex.exe")
    build = os.path.join(root, "_doc", "sphinxdoc","build","latex")
    for tex in os.listdir(build):
        if tex.endswith(".tex") and (afile is None or afile in tex):
            file = os.path.join(build, tex)
            if doall :
                c = '"{0}" "{1}" -output-directory="{2}"'.format(lat, file, build) #  -interaction=batchmode
            else :
                c = '"{0}" "{1}" -interaction=batchmode -output-directory="{2}"'.format(lat, file, build) 
            fLOG("   ** LATEX compilation (c)", c) 
            post_process_latex_output(file, doall)
            out,err = run_cmd(c,wait=True, do_not_log = False, log_error=False)
            if len(err) > 0 :
                raise HelpGenException(err)
            # second compilation
            fLOG("   ** LATEX compilation (d)", c) 
            out,err = run_cmd(c,wait=True, do_not_log = False, log_error=False)
            if len(err) > 0 :
                raise HelpGenException(err)
