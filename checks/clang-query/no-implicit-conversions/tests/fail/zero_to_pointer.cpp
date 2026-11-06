struct Base
{
};

void take_pointer(const Base *);

void pass_zero() { take_pointer(0); }// expect-finding
