struct Base
{
};

template<typename T> struct Holder
{
  template<typename Other> Holder(const Holder<Other> &);// NOLINT(google-explicit-constructor)

  Holder() = default;
};

void take_holder(const Holder<Base> &);
void take_by_value(Base);
void take_pointer(const Base *);
void take_double(double);

void pass_exact_types(const double value)
{
  take_holder(Holder<Base>());
  take_by_value(Base{});
  take_pointer(nullptr);
  take_double(value);
}
