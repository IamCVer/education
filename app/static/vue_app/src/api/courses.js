import request from '@/utils/request'

export default {
    // 获取我的课程列表（教师）
    getMyCourses() {
        return request.get('/api/v1/courses')
    },

    // 获取所有已发布的课程（学生）
    getPublishedCourses() {
        return request.get('/api/v1/courses', {
            params: { published_only: true }
        })
    },

    // 获取课程详情（包含视频列表）
    getCourseDetail(id) {
        return request.get(`/api/v1/courses/${id}`)
    },

    // 创建课程
    createCourse(data) {
        return request.post('/api/v1/courses', data)
    },

    // 更新课程
    updateCourse(id, data) {
        return request.put(`/api/v1/courses/${id}`, data)
    },

    // 删除课程
    deleteCourse(id) {
        return request.delete(`/api/v1/courses/${id}`)
    }
}
