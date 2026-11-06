[[nodiscard]] const unsigned char *object_bytes(const int &value)
{
  return (const unsigned char *)&value;// expect-finding
}
