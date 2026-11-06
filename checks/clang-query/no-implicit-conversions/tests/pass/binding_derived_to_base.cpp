struct Base
{
};
struct Derived : Base
{
};

void take_base(const Base &);
void take_base(const Base *);

void bind_derived()
{
  const auto derived = Derived{};
  take_base(&derived);
  take_base(Derived{});
  take_base(derived);
}
