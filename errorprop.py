
class errorpropogation: 
    """A tuple-based error propogation class to add, subtract, multiply, divide, and take powers without worry. 
    Uses linear forms of error propagation and neglects correlation."""
    def __init__(self): 
        self.temp = []

    #TODO expand to allow for any number of inputs....therefore letting you add 3 things at once, etc.

    def add(self,tup1,tup2): 
        a,aerr,b,berr = tup1[0],tup1[1],tup2[0],tup2[1]
        c = a + b
        cerr = (aerr**2+berr**2)**0.5
        return (c, cerr)

    def sub(self,tup1,tup2): 
        a,aerr,b,berr = tup1[0],tup1[1],tup2[0],tup2[1]
        c = a - b
        cerr = (aerr**2+berr**2)**0.5
        return (c, cerr)

    def mult(self,tup1,tup2): 
        a,aerr,b,berr = tup1[0],tup1[1],tup2[0],tup2[1]
        c = a*b
        cerr = abs(c*((aerr/a)**2+(berr/b)**2)**0.5)
        return (c, cerr)

    def div(self,tup1,tup2): 
        a,aerr,b,berr = tup1[0],tup1[1],tup2[0],tup2[1]
        c = a/b
        cerr = abs(c*((aerr/a)**2+(berr/b)**2)**0.5)
        return (c, cerr)

    def multC(self,cst,tup1):
        a,aerr = tup1[0],tup1[1]
        c = a*cst
        cerr = abs(aerr*cst)
        return (c,cerr)
    
    def powC(self,cst,tup1): 
        a,aerr = tup1[0],tup1[1]
        c = a**cst
        cerr = abs((cst*c)*(aerr/a)) # aka cerr = abs(abs(cst*a**(cst-1))*aerr)
        return (c,cerr)
    