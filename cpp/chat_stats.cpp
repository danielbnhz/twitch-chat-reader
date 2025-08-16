// chat_stats.cpp
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <map>
#include <vector>
#include <sstream>
#include <algorithm>
#include <cctype>

namespace py = pybind11;

// Structure to hold user statistics
struct UserStats {
    double avg_words = 0.0;
    double caps_ratio = 0.0;
};

// Function to calculate stats
std::map<std::string, UserStats> analyze_chat(const std::vector<std::string>& messages) {
    std::map<std::string, std::vector<std::string>> user_messages;

    // Split messages by "username: message" format
    for (const auto& msg : messages) {
        auto pos = msg.find(":");
        if (pos != std::string::npos) {
            std::string user = msg.substr(0, pos);
            std::string text = msg.substr(pos + 1);
            user_messages[user].push_back(text);
        }
    }

    std::map<std::string, UserStats> stats;

    // Calculate stats for each user
    for (const auto& [user, msgs] : user_messages) {
        size_t total_words = 0;
        size_t total_chars = 0;
        size_t uppercase_chars = 0;

        for (const auto& text : msgs) {
            std::istringstream iss(text);
            size_t word_count = std::distance(std::istream_iterator<std::string>(iss),
                                             std::istream_iterator<std::string>());
            total_words += word_count;

            for (char c : text) {
                if (std::isalpha(static_cast<unsigned char>(c))) {
                    total_chars++;
                    if (std::isupper(static_cast<unsigned char>(c))) {
                        uppercase_chars++;
                    }
                }
            }
        }

        size_t msg_count = msgs.size();
        UserStats ustat;
        ustat.avg_words = msg_count > 0 ? static_cast<double>(total_words) / msg_count : 0.0;
        ustat.caps_ratio = total_chars > 0 ? static_cast<double>(uppercase_chars) / total_chars : 0.0;

        stats[user] = ustat;
    }

    return stats;
}

// Pybind11 module
PYBIND11_MODULE(chat_stats, m) {
    m.doc() = "Analyze Twitch chat: average words per user and caps ratio";

    py::class_<UserStats>(m, "UserStats")
        .def_readonly("avg_words", &UserStats::avg_words)
        .def_readonly("caps_ratio", &UserStats::caps_ratio);

    m.def("analyze_chat", &analyze_chat,
          py::arg("messages"),
          "Analyze chat messages per user");
}
