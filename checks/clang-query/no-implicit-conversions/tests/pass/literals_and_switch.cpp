void take_string(const char *);

[[nodiscard]] int classify(const char value)
{
  take_string("literal");
  [[maybe_unused]] const long widened = 1;

  switch (value) {
  case 'a':
    return 1;
  default:
    return 0;
  }
}
