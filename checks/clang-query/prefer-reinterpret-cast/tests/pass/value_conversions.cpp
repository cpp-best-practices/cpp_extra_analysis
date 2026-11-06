struct Base
{
  int base_value;
};

struct Derived : Base
{
  int derived_value;
};

using integer = int;

[[nodiscard]] constexpr int truncate(const double value) { return (int)value; }

[[nodiscard]] constexpr int truncate_functional(const double value) { return integer(value); }

[[nodiscard]] const Derived *as_derived(const Base *base) { return (const Derived *)base; }

[[nodiscard]] const Base *as_base(const Derived *derived) { return (const Base *)derived; }

[[nodiscard]] float to_float(const int &value) { return (const float &)value; }
