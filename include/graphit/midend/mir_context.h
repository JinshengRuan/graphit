//
// Created by Yunming Zhang on 2/12/17.
//

#ifndef GRAPHIT_PROGRAM_CONTEXT_H
#define GRAPHIT_PROGRAM_CONTEXT_H

#include <memory>
#include <string>
#include <vector>
#include <list>
#include <map>
#include <utility>

#include <graphit/midend/mir.h>

namespace graphit {


        // Data structure that holds the internal representation of the program
        class MIRContext {

        public:
            MIRContext() {
            }


            ~MIRContext() {
            }

            //void setProgram(mir::Stmt::Ptr program){this->mir_program = program};
//            void addStatement(mir::Stmt::Ptr stmt){
//                statements.push_back(stmt);
//            }

//            std::vector<mir::Stmt::Ptr> getStatements(){
//                return statements;
//            }

        private:
            //mir::Program::Ptr mir_program;
            std::vector<mir::Stmt::Ptr> constants;
        };

}

#endif //GRAPHIT_PROGRAM_CONTEXT_H
