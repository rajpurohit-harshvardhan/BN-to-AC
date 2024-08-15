This file provides the information for the execution of the program to convert any Bayesian Network(BN) with its BIF file to the corresponding AC. The _main.py_ file needs to be executed. The input required for the project is the **absolute path of the bif file** for which the conversion is to be executed. The `bif_file` variable is where the path needs to be mentioned. The command below this `bif_file` variable is the function call to the main function using the `bif_file` and `evidence` variables. For inferencing, the network, this `evidence` variable needs to be provided with the appropriate values.
 
The format for providing evidence is "**(Variable-Name)=(Variable-Value)**" which needs to be in a string format. For providing more than one evidence value, the values should be separated with a comma (,) in between. 

**NOTE**: The evidence variables and values should follow the same format mentioned in the BIF file. Differing evidence values would simply execute the code by turning every indicator on, thus resulting in 1.0 at the root node.

An example of evidence for the Asia Bayesian network is:

`evidence='asia=yes'` OR
`evidence='xray=no,lung=yes'` 

in terms of the function call it would simply be:

`main(bif_file, 'xray=no,lung=yes')`

Once the execution of _main.py_ file is finished, a folder namely ***arithmetic-circuits*** would be created containing additional folders and files. A folder with the **name of the BIF file**, provided in the beginning, would appear in this **arithmetic-circuits** folder whose contents are a DOT file, representing the arithmetic circuit, and an SVG file of the plotted directed graph for the arithmetic circuit. 

**NOTE:** The program executes successfully for smaller Bayesian networks only, particularly the ones with **number of nodes not more than 10**. We will be working on refactoring the code and simplifying it to make it work for medium, large as well as massive networks.

A sample of the output for the execution of the file is provided below:

`Evaluation of Arithmetic circuit yields asia: 1.0` //final value for testing the BN by turning every indicator on

`Evaluation of Arithmetic Circuit based on evidence xray=no,lung=yes yields ::  0.00011` //output value for the evidence provided

`Created arithmetic circuit at folder: arithmetic-circuits/asia`
`Nodes statistics :: {'total': 203, 'product': 110, 'sum': 41, 'parameter': 36, 'indicator': 16}` // calculated stats for the converted AC