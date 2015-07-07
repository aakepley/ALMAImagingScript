def strip_instructions(infilename, outfilename):

    """
    This function runs within CASA.

    It removes the instructions to the data imager from the scriptForImaging_template.py
    Takes in two string variables infilename and outfilename.
    It is perferable that the file names are not the same.
    
    Example: From within CASA
	execfile('strip_instructions')
	strip_instructions('scriptForImaging_template.py','scriptForImaging.py') 
    """
    
    import shutil
    
    if infilename == outfilename:
        # TESTING -- CU
        print "infilename equals outfilename!"

	backup='scripForImaging_backup.py'
        print "Creating a backup of scripForImaging.py: "+backup
        shutil.copyfile(infilename,backup)
        
        tempfilename = 'scripForImaging_input.py'
        shutil.copyfile(infilename,tempfilename)
        
        infilename=tempfilename
   
    print "New input file name: "+infilename
    print "Output file name: "+outfilename
 
    infile = open(infilename,'r')
    outfile = open(outfilename, 'w')

    for line in infile:
        if line.startswith('#>>>'):
            continue
        else:
            outfile.write(line)

    infile.close()
    outfile.close()
