def strip_instructions(infilename):

    """
    This function removes the instructions to the data imager from the
    scriptForImaging_template.py. It takes a string giving the name of
    the input file and will produce a backup file with the original
    script and a new file with the instructions to the data imager
    removed.
    
    Example: 
	execfile('strip_instructions')
    	strip_instructions('scriptForImagingPrep_template.py') 
	strip_instructions('scriptForImaging_template.py') 
    """
    
    import shutil
    import os.path

    backupfilename = infilename + '.backup'

    if os.path.isfile(backupfilename):
        print "Backup file exists! Stopping."
        return
    else:
        print "Moving " + infilename + " to " + backupfilename +"."
        shutil.move(infilename,backupfilename)
        outfilename = infilename
        infilename = backupfilename
         
    infile = open(infilename,'r')
    outfile = open(outfilename, 'w')

    print "Stripping instructions"
    for line in infile:
        if line.startswith('#>>>'):
            continue
        else:
            outfile.write(line)

    infile.close()
    outfile.close()
