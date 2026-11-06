struct istream
{
  explicit operator bool() const;
  [[nodiscard]] bool good() const;
};

void take_double(double);

void convert_explicitly(const istream &input, const int value)
{
  while (input.good()) {}
  take_double(static_cast<double>(value));
  [[maybe_unused]] const bool valid = static_cast<bool>(input);
}
