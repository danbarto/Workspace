#ifndef Workspace_FWLite_StringTools_H
#define Workspace_FWLite_StringTools_H

#include <string>
#include <list>

namespace StringTools {
  /** some helper functions to manipulate strings **/

  /// how many qoutes are there in <src> up to position <pos>? 
  int number_quotes ( const std::string & src, std::string::size_type pos );

  /// find <sub> in <src> but only if it's not preceded by a backslash
  std::string::size_type find_unescaped( const std::string & src, const std::string & sub );

  /// split up <source> at every <sep>, returning a list of tokens
  std::list< std::string > msplit( std::string source, std::string sep );
}

#endif
