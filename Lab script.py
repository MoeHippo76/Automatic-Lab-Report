from matplotlib import pyplot as plt
import sympy as sym
import numpy as np
import yaml

def makeLatexTable(n,label,caption):
    with open("latex_features/"+"table.tex") as fp:
        contents = fp.readlines()
    str_ncols = "|"
    for _ in range(n):
        str_ncols += "c|"
    for i,line in enumerate(contents):
            if "begin" in line and "tabular" in line:
                line = line[:-1]+"{"+str_ncols+"}"
                contents[i] = line
            if "caption" in line:
                line = line[:-1] + "{" + caption + "}\n"
                contents[i] = line
            if "label" in line:
                line = line[:-1] + "{" + label + "}\n"
                contents[i] = line
    fp.close()
    return contents

def makeTable(result_file):
    with open(result_file) as fp:
        contents = fp.readlines()
        
        hlineStr = "\t\hline\n"
        table_rows = ["\n"+hlineStr]

        header =  contents[0].split(',')
        header[-1] = header[-1][:-1]
        for i,head in enumerate(header):
            header[i] = "$" + sym.latex(sym.core.sympify(head)) +"$"
        contents[0] = ','.join(header) +"\n"
        n = len(header)
        caption =  header[-1]  + " against "  + header[0]
        label = "tab:"+header[-1]
        for line in contents:
            data = line.split(',')
            line = " & ".join(data)
            string = "\t" + line[:-1] + "\\\\" +"\n"+hlineStr
            table_rows.append(string)

    table_lines = makeLatexTable(n,label,caption)

    for i,line in enumerate(table_lines):
        if "begin" in line and "tabular" in line:
            break
    for row in table_rows:
        i+=1
        table_lines.insert(i,row)
    return table_lines

def makeGraph(result_file):

    with open(result_file) as fp:
        contents = fp.readlines()
        header =  contents[0].split(',')
        header[-1] = header[-1][:-1]
        for i,head in enumerate(header):
            header[i] = sym.latex(sym.core.sympify(head))
        title = header[-1] + " against " + header[0]
        caption = "$" + header[-1] + "$" + " against " + "$" + header[0] + "$"
        label = "fig:"+header[-1]
        x = []
        y = []
        for line in contents[1:]:
            data = line.split(',')
            x.append(float(data[0]))
            y.append(float(data[-1][:-1]))
        
    plt.figure(title)
    plt.plot(x,y)
    plt.title(title)
    plt.xlabel(header[0])
    plt.ylabel(header[-1])
    plt.savefig("output/"+title+".png")
    return makeLatexGraph(label,caption,title)

def makeLatexGraph(label,caption,title):
    with open("latex_features/figure.tex") as fp:
        contents = fp.readlines()
        for i,line in enumerate(contents):
            if "includegraphics" in line:
                line = line[:-1]+"{"+title+".png}\n"
                contents[i] = line
            if "caption" in line:
                line = line[:-1] + "{" + caption + "}\n"
                contents[i] = line
            if "label" in line:
                line = line[:-1] + "{" + label + "}\n"
                contents[i] = line
    return contents

def makeEquation(symbol,expression):
    latex_expr = "\t" + sym.latex(symbol) + " = " + sym.latex(expression) + "\n"
    label = "eq:"+ str(symbol)
    with open("latex_features/equation.tex") as fp:
        contents = fp.readlines()
        for i,line in enumerate(contents):
            if "begin"  in line:
                contents.insert(i+1,latex_expr)
            if "label" in line:
                line = line[:-1] + "{" + label + "}\n"
                contents[i] = line
    return contents

def writeTheory():
    global lab_contents
    for i,line in enumerate(lab_contents):
        if "Theory" in line:
            break
    index = i
    
    for symb,expr in equations.items():
        equation = makeEquation(sym.symbols(symb),expr)
        for eq_line in equation:
            index +=1
            lab_contents.insert(index,eq_line)
    return lab_contents

def performAnalysis(analysis_obj,const_exist):
    global equations 
    
    expr_key = analysis_obj["calculate"]
    input_table =   analysis_obj["input table"]
    input_columns = analysis_obj["input columns"]
    
    expr = equations[expr_key]

    if const_exist:
        consts = analysis_obj["constants"]
        expr = expr.subs(consts)   

    symbols = list(expr.free_symbols)
    f = sym.utilities.lambdify(symbols,expr,modules=np)

    with open("data/"+input_table) as fp:
        contents = fp.readlines()
        outputs = []
        inputs = []
        for line in contents[1:]:
            data = line.split(',')

            input = []
            for i in input_columns.split(","):
                input.append(float(data[int(i)]))
            output = round(f(*tuple(input)),3)
            outputs.append(output)
            inputs.append(input)

    output_file = "data/"+expr_key + ".csv"
    with open(output_file,'w') as fp:
        header = ""
        for symb in symbols:
            header += str(symb) + ","
        header += expr_key + "\n"
        fp.write(header)
        for i in range(len(contents) - 1):
            entry = ""
            for inp in inputs[i]:
                entry += str(inp) + ","
            entry += str(outputs[i]) + "\n"
            fp.write(entry)
    return output_file

def writeData(section,file,index = -1):
    global lab_contents
    for i,line in enumerate(lab_contents):
        if section in line:
            break
    if index == -1:
        index = i

    result_file = file
    table = makeTable(result_file)
    for table_line in table:
        index +=1
        lab_contents.insert(index,table_line)
    graph = makeGraph(result_file)
    
    for graph_line in graph:
        index +=1
        lab_contents.insert(index,graph_line)

    return index


if __name__ == "__main__":
    global equations,lab_contents
    
    with open("lab_config.yaml") as fp:
        settings = yaml.full_load(fp) 
        equations = {k:sym.core.sympify(v) for k, v in settings["equations"].items()}
        results = settings["results"]
        analysis = settings["analysis"]

    with open("latex_features/lab.tex") as fp:
        lab_contents = fp.readlines()
        writeTheory()
        
        i = -1
        for result in results:
            i = writeData("Results","data/"+result,i)
        
        i = -1
        for k in analysis.keys():
            an = analysis[k]
            const_exist = "constants" in an
            ofile = performAnalysis(an,const_exist)
            i = writeData("Analysis",ofile,i)
        
        with open("output/main.tex","w") as fp:
            fp.writelines(lab_contents)