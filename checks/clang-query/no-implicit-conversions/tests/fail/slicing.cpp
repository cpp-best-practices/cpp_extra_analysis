struct Base
{
};
struct Derived : Base
{
};

void take_by_value(Base);

void slice_derived()
{
  const auto derived = Derived{};

  take_by_value(derived);// expect-finding
  [[maybe_unused]] const Base sliced = derived;// expect-finding
  take_by_value(Derived{});// expect-finding
}
