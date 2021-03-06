"""
@file
@brief Subpart related to the documentation generation.
"""

def get_help_usage():
    """
    returns the usage ``python setup.py build_sphinx``
    """
    return """
        This command will build the documentation form the source.
        It will not work from the installed package.
        This is a custom build, the regular options with build_sphinx will not work.
        The output will be copied in folder dist.
        
        Usage:
        
            python setup.py build_sphinx
        """.replace("        ","")
