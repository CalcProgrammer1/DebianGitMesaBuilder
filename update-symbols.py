import os

for file in os.listdir("./debian"):
        name, ext = os.path.splitext(file)
        if(ext == ".symbols"): 
                os.system("dpkg-gensymbols -p" + name + " -Pdebian/" + name + " -Odebian/" + name + ".symbols")

