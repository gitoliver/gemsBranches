prefSTRUCTURE='mol'  # default prefix for a structure file

##
## File Extensions - the part after the final period (.)
##
# General extensions
extPDB='pdb'  # all varieties of PDB-style file
extOFF='off'  # OFF files
extMMCIF='mmcif'  # mm-cif files
extMOL2='mol2' # mol2 files.
extTEXT='txt'  # A plain-text file, usually ASCII
extRUNLOG='runlog'  # log for the GLYCAM-Web process

# AMBER-related extensions
extPARM='parm7'  # AMBER parameter-topology file
extINPCRD='rst7'  # AMBER input-coordinate file
extMINCRD='mincrd'
extHEATCRD='heatcrd'
extEQUICRD='equicrd'
extMDCRD='mdcrd'  # AMBER coordinate trajectory
extMDVEL='mdvel'  # AMBER velocity trajectory
extMDCRDBOX='crdbox'  # AMBER coordinate trajectory with periodic boundary

extCPPTRAJIN='cpptrajin'
extLEAPIN='leapin'
extMININ='minin'
extHEATIN='heatin'
extEQUIIN='equiin'
extMDIN='mdin'  # AMBER molecular dynamics input file

extMINOUT='minout'
extHEATOUT='heatout'
extEQUIOUT='equiout'
extMDOUT='mdout'  # AMBER molecular dynamics output file

extMDCRDREF='rst7'  # AMBER molecular dynamics reference coordinate file
extMDRST='rst7'  # AMBER molecular dynamics reference coordinate file

extMININFO='mininfo'
extHEATINFO='heatinfo'
extEQUIINFO='equiinfo'
extMDINFO='mdinfo'  # AMBER molecular dynamics simulation information file

extMINLOG='minlog'
extHEATLOG='heatlog'
extEQUILOG='equilog'
extMDLOG='mdlog'  # AMBER molecular dynamics simulation log file
# Docking-related extensions
# Grafting-related extensions

##
## Modifiers - separated by underscores
##
modAMBER='AMBER'  # non-AMBER files formatted for use with AMBER utilities
modION='Ion'  # a structure containing a charged molecule with counter-ions
modSOLV='Sol' # a solvated structure
modNOH='noh'  # a structure file from which hydrogens have been removed

##
## Global Names - do not change with project
##
SMAP_Actual='Structure_Mapping_Table.txt' # maps rotamers to directory names, 
                                          # Official version, touched only by wev server.
SMAP='Shadow_Mapping_Table.txt'  # copy of SMAP_Actual, used by submission scripts
FFINFO='Force_Field_Info.txt' # lists force fields used to generate structures
GVIZ='Graphviz_SNFG_script.dot' # file used to make the SNFG image
RMAP='Residue_Mapping_Table.txt' # Maps input PDB residues to output residues
SNFG_SVG='SNFG.svg' # SVG file of the SNFG image
SNFG_PNG='SNFG.png' # PNG file of the SNFG image
SUB_OSM_PREF='Run' # Submission script prefix, OS-modeling

