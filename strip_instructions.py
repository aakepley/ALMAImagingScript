def strip_instructions(infilename, outfilename):

    """
    Remove the instructions to the data imager from the scriptForImaging_template.py
    """
    
    import shutil
    
    if infilename == outfilename:
        # TESTING -- CU
        print "infilename equals outfilename!"
        print "Creating a backup of scripForImaging.py"
        backup=infilename+'.backup.py'
        shutil.copyfile(infilename,backup)
        
        tempfilename = infilename+'.temp'
        tempfile = shutil.move(infilename,tempfilename)
        
        infilename=temfile
    
    infile = open(infilename,'r')
    outfile = open(outfilename, 'w')

    for line in infile:
        if line.startswith('#>>>'):
            continue
        else:
            outfile.write(line)

    infile.close()
    outfile.close()
    
help(strip_instructions)
strip_instructions()
    This function runs within CASA.
    Takes in two string variables infilename and outfilename.
    It is perferable that the file names are not the same.
    
    Example: From within CASA
        execfile('strip_instructions')
        strip_instructions('scriptForImaging_template.py','scriptForImaging.py') 
        

    
