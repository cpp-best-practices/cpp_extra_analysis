template<typename Char> struct basic_string
{
  basic_string(const Char *);// NOLINT(google-explicit-constructor)
  basic_string(const basic_string &);
  ~basic_string();
  [[nodiscard]] const Char *c_str() const;
};

using string = basic_string<char>;

string copy_through_c_str(const string &value)
{
  return value.c_str();// expect-finding
}
