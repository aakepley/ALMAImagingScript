def strip_instructions(infilename='scriptForImaging_template.py', outfilename='scriptForImaging.py'):

    """
    Remove the instructions to the data imager from the scriptForImaging_template.py
    """
    

    infile = open(infilename,'r')
    outfile = open(outfilename, 'w')

    for line in infile:
        if line.startswith('#>>>'):
            continue
        else:
            outfile.write(line)

    infile.close()
    outfile.close()
    
