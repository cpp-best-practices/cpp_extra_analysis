using byte_pointer = const unsigned char *;

[[nodiscard]] byte_pointer object_bytes(const int &value)
{
  return byte_pointer(&value);// expect-finding
}
