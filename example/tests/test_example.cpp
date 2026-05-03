#include <cassert>
#include <string>

#include "example/greeting.hpp"

int main() {
    assert(std::string(example::project_slug()) == "insurgent-example");
    const std::string line = example::greeting_line();
    assert(line.find("Hello") != std::string::npos);
    assert(line.find("InsurgeNT") != std::string::npos);
    return 0;
}
