struct Base
{
};
struct Derived : Base
{
};

template<typename T> struct Holder
{
  template<typename Other> Holder(const Holder<Other> &);// NOLINT(google-explicit-constructor)

  Holder() = default;
};

void take_holder(const Holder<Base> &);

void pass_converted_holders()
{
  const auto derived = Holder<Derived>{};
  take_holder(derived);// expect-finding
  take_holder(Holder<Derived>());// expect-finding
}
