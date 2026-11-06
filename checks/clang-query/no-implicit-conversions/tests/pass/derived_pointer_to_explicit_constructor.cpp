struct Base
{
};
struct Derived : Base
{
};

struct Observer
{
  explicit Observer(const Base *);
};

void observe(const Derived &derived) { [[maybe_unused]] const Observer observer(&derived); }
